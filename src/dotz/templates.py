"""Template and Profile management for dotz - a Git-backed dotfiles manager."""

import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import DOTZ_DIR, WORK_TREE, console, ensure_repo
from .exceptions import (
    DotzArchiveError,
    DotzFileNotFoundError,
    DotzProfileError,
    DotzSecurityError,
    DotzTemplateError,
    ProfileMetadataDict,
    TemplateMetadataDict,
)

# Constants
TEMPLATES_DIR_NAME = "templates"
PROFILES_DIR_NAME = "profiles"
TEMPLATE_METADATA_FILE = "template.json"
PROFILE_METADATA_FILE = "profile.json"
ACTIVE_PROFILE_FILE = "active_profile"

# Global paths
TEMPLATES_DIR = DOTZ_DIR / TEMPLATES_DIR_NAME
PROFILES_DIR = DOTZ_DIR / PROFILES_DIR_NAME
ACTIVE_PROFILE_PATH = DOTZ_DIR / ACTIVE_PROFILE_FILE


# ============================================================================
# TEMPLATE MANAGEMENT
# ============================================================================


def get_templates_dir() -> Path:
    """Get the templates directory, creating it if necessary."""
    TEMPLATES_DIR.mkdir(exist_ok=True)
    return TEMPLATES_DIR


def get_profiles_dir() -> Path:
    """Get the profiles directory, creating it if necessary."""
    PROFILES_DIR.mkdir(exist_ok=True)
    return PROFILES_DIR


def list_templates() -> List[TemplateMetadataDict]:
    """List all available templates with their metadata."""
    templates = []
    templates_dir = get_templates_dir()

    for template_path in templates_dir.iterdir():
        if template_path.is_dir():
            metadata_file = template_path / TEMPLATE_METADATA_FILE
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    metadata["path"] = template_path
                    templates.append(metadata)
                except (json.JSONDecodeError, KeyError):
                    # Create basic metadata for corrupted templates
                    templates.append(
                        {
                            "name": template_path.name,
                            "description": "Template with corrupted metadata",
                            "created": "unknown",
                            "files": [],
                            "path": template_path,
                        }
                    )

    return sorted(templates, key=lambda t: t.get("created", ""))


def create_template(
    name: str,
    description: str = "",
    files: Optional[List[str]] = None,
    quiet: bool = False,
) -> bool:
    """Create a new template from specified files or current tracked files."""
    try:
        templates_dir = get_templates_dir()
        template_path = templates_dir / name

        if template_path.exists():
            if not quiet:
                console.print(f"[red]Template '{name}' already exists[/red]")
            return False

        # Get files to include in template
        if files is None:
            # Use all currently tracked files
            repo = ensure_repo()
            tracked_files = repo.git.ls_files().splitlines()
            files = tracked_files

        if not files:
            if not quiet:
                console.print("[yellow]No files to include in template[/yellow]")
            return False

        # Create template directory
        template_path.mkdir(parents=True)

        # Copy files to template
        template_files_dir = template_path / "files"
        template_files_dir.mkdir()

        copied_files = []
        for file_rel in files:
            source_file = WORK_TREE / file_rel
            if source_file.exists():
                dest_file = template_files_dir / file_rel
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)
                copied_files.append(file_rel)

        # Create template metadata
        metadata = {
            "name": name,
            "description": description,
            "created": datetime.now().isoformat(),
            "files": copied_files,
            "file_count": len(copied_files),
            "created_by": "dotz",
            "version": "1.0",
        }

        metadata_file = template_path / TEMPLATE_METADATA_FILE
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        if not quiet:
            console.print(
                f"[green]✓ Template '{name}' created with "
                f"{len(copied_files)} files[/green]"
            )

        return True

    except DotzTemplateError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error creating template: {e}[/red]")
        raise DotzTemplateError(f"Failed to create template: {e}") from e


def apply_template(
    name: str, merge: bool = False, backup: bool = True, quiet: bool = False
) -> bool:
    """Apply a template to the current dotz repository."""
    try:
        templates_dir = get_templates_dir()
        template_path = templates_dir / name

        if not template_path.exists():
            if not quiet:
                console.print(f"[red]Template '{name}' not found[/red]")
            return False

        metadata_file = template_path / TEMPLATE_METADATA_FILE
        if not metadata_file.exists():
            if not quiet:
                console.print(f"[red]Template '{name}' has no metadata[/red]")
            return False

        # Load template metadata
        with open(metadata_file) as f:
            metadata = json.load(f)

        template_files_dir = template_path / "files"
        if not template_files_dir.exists():
            if not quiet:
                console.print(f"[red]Template '{name}' has no files[/red]")
            return False

        repo = ensure_repo()

        # Create backup if requested
        if backup and not merge:
            backup_name = (
                f"pre_template_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            if not _create_repo_backup(backup_name, quiet):
                if not quiet:
                    console.print("[yellow]Warning: Could not create backup[/yellow]")

        applied_files = []
        skipped_files = []

        # Apply template files
        for file_rel in metadata.get("files", []):
            source_file = template_files_dir / file_rel
            dest_file = WORK_TREE / file_rel

            if not source_file.exists():
                skipped_files.append(file_rel)
                continue

            # Check if file exists and handle merge mode
            if dest_file.exists() and not merge:
                # Overwrite existing file
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)
                applied_files.append(file_rel)
            elif not dest_file.exists():
                # Copy new file
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)
                applied_files.append(file_rel)
            else:
                # File exists and merge mode - skip
                skipped_files.append(file_rel)

        # Stage and commit applied files
        if applied_files:
            repo.index.add(applied_files)
            commit_message = f"Apply template '{name}'"
            if merge:
                commit_message += " (merge mode)"
            repo.index.commit(commit_message)

        if not quiet:
            console.print(f"[green]✓ Template '{name}' applied[/green]")
            console.print(f"  Applied: {len(applied_files)} files")
            if skipped_files:
                console.print(f"  Skipped: {len(skipped_files)} files")

        return True

    except DotzTemplateError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error applying template: {e}[/red]")
        raise DotzTemplateError(f"Failed to apply template: {e}") from e


def delete_template(name: str, quiet: bool = False) -> bool:
    """Delete a template."""
    try:
        templates_dir = get_templates_dir()
        template_path = templates_dir / name

        if not template_path.exists():
            if not quiet:
                console.print(f"[red]Template '{name}' not found[/red]")
            return False

        shutil.rmtree(template_path)

        if not quiet:
            console.print(f"[green]✓ Template '{name}' deleted[/green]")

        return True

    except DotzTemplateError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error deleting template: {e}[/red]")
        raise DotzTemplateError(f"Failed to delete template: {e}") from e


def export_template(name: str, output_path: str, quiet: bool = False) -> bool:
    """Export a template as a portable archive."""
    try:
        templates_dir = get_templates_dir()
        template_path = templates_dir / name

        if not template_path.exists():
            if not quiet:
                console.print(f"[red]Template '{name}' not found[/red]")
            return False

        output_file = Path(output_path)
        if output_file.suffix != ".tar.gz":
            output_file = output_file.with_suffix(".tar.gz")

        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(template_path, arcname=name)

        if not quiet:
            console.print(
                f"[green]✓ Template '{name}' exported to {output_file}[/green]"
            )

        return True

    except DotzArchiveError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error exporting template: {e}[/red]")
        raise DotzArchiveError(f"Failed to export template: {e}") from e


def import_template(archive_path: str, quiet: bool = False) -> bool:
    """Import a template from an archive."""
    try:
        templates_dir = get_templates_dir()
        archive_file = Path(archive_path)

        if not archive_file.exists():
            if not quiet:
                console.print(f"[red]Archive '{archive_path}' not found[/red]")
            raise DotzFileNotFoundError(f"Archive '{archive_path}' not found")

        with tarfile.open(archive_file, "r:gz") as tar:
            # Validate archive members for security (prevent path traversal attacks)
            def is_safe_member(member: tarfile.TarInfo) -> bool:
                """Check if a tar member is safe to extract."""
                # Only allow regular files and directories
                if not (member.isfile() or member.isdir()):
                    return False

                # Check for directory traversal attempts
                if ".." in member.name or member.name.startswith("/"):
                    raise DotzSecurityError(
                        f"Path traversal attempt detected: {member.name}"
                    )

                # Construct the full extraction path
                try:
                    extract_path = (templates_dir / member.name).resolve()
                    # Ensure the path stays within the templates directory
                    extract_path.relative_to(templates_dir.resolve())
                    return True
                except (ValueError, OSError) as e:
                    raise DotzSecurityError(
                        f"Unsafe extraction path: {member.name}"
                    ) from e

            # Filter out unsafe members and extract them individually
            for member in tar.getmembers():
                if is_safe_member(member):
                    try:
                        tar.extract(member, templates_dir)
                    except Exception as extract_error:
                        if not quiet:
                            console.print(
                                f"[yellow]Failed to extract {member.name}: "
                                f"{extract_error}[/yellow]"
                            )
                else:
                    if not quiet:
                        console.print(
                            f"[yellow]Skipping unsafe member: {member.name}[/yellow]"
                        )

        if not quiet:
            console.print(f"[green]✓ Template imported from {archive_file}[/green]")

        return True

    except (DotzArchiveError, DotzSecurityError, DotzFileNotFoundError):
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error importing template: {e}[/red]")
        raise DotzArchiveError(f"Failed to import template: {e}") from e


# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================


def list_profiles() -> List[ProfileMetadataDict]:
    """List all available profiles with their metadata."""
    profiles = []
    profiles_dir = get_profiles_dir()

    for profile_path in profiles_dir.iterdir():
        if profile_path.is_dir():
            metadata_file = profile_path / PROFILE_METADATA_FILE
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    metadata["path"] = profile_path
                    profiles.append(metadata)
                except (json.JSONDecodeError, KeyError):
                    # Create basic metadata for corrupted profiles
                    profiles.append(
                        {
                            "name": profile_path.name,
                            "description": "Profile with corrupted metadata",
                            "created": "unknown",
                            "active": False,
                            "path": profile_path,
                        }
                    )

    # Mark active profile
    active_profile = get_active_profile()
    for profile in profiles:
        profile["active"] = profile["name"] == active_profile

    return sorted(profiles, key=lambda p: p.get("created", ""))


def create_profile(
    name: str,
    description: str = "",
    environment: str = "",
    copy_from: Optional[str] = None,
    quiet: bool = False,
) -> bool:
    """Create a new profile."""
    try:
        profiles_dir = get_profiles_dir()
        profile_path = profiles_dir / name

        if profile_path.exists():
            if not quiet:
                console.print(f"[red]Profile '{name}' already exists[/red]")
            return False

        # Create profile directory
        profile_path.mkdir(parents=True)

        # Create profile structure
        (profile_path / "files").mkdir()
        (profile_path / "config").mkdir()

        # Copy from existing profile if specified
        if copy_from:
            source_profile_path = profiles_dir / copy_from
            if source_profile_path.exists():
                # Copy files and config
                source_files = source_profile_path / "files"
                source_config = source_profile_path / "config"

                if source_files.exists():
                    shutil.copytree(
                        source_files, profile_path / "files", dirs_exist_ok=True
                    )
                if source_config.exists():
                    shutil.copytree(
                        source_config, profile_path / "config", dirs_exist_ok=True
                    )

        # Create profile metadata
        metadata = {
            "name": name,
            "description": description,
            "environment": environment,
            "created": datetime.now().isoformat(),
            "created_by": "dotz",
            "version": "1.0",
            "last_used": None,
            "active": False,
        }

        metadata_file = profile_path / PROFILE_METADATA_FILE
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        if not quiet:
            console.print(f"[green]✓ Profile '{name}' created[/green]")

        return True

    except DotzProfileError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error creating profile: {e}[/red]")
        raise DotzProfileError(f"Failed to create profile: {e}") from e


def switch_profile(name: str, backup: bool = True, quiet: bool = False) -> bool:
    """Switch to a different profile."""
    try:
        profiles_dir = get_profiles_dir()
        profile_path = profiles_dir / name

        if not profile_path.exists():
            if not quiet:
                console.print(f"[red]Profile '{name}' not found[/red]")
            return False

        current_profile = get_active_profile()

        # Save current state to current profile
        if current_profile and backup:
            if not _save_current_state_to_profile(current_profile, quiet):
                if not quiet:
                    console.print(
                        "[yellow]Warning: Could not save current state[/yellow]"
                    )

        # Apply new profile
        if not _apply_profile_state(name, quiet):
            return False

        # Update active profile
        with open(ACTIVE_PROFILE_PATH, "w") as f:
            f.write(name)

        # Update profile metadata
        metadata_file = profile_path / PROFILE_METADATA_FILE
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
            metadata["last_used"] = datetime.now().isoformat()
            metadata["active"] = True
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

        if not quiet:
            console.print(f"[green]✓ Switched to profile '{name}'[/green]")

        return True

    except DotzProfileError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error switching profile: {e}[/red]")
        raise DotzProfileError(f"Failed to switch profile: {e}") from e


def get_active_profile() -> Optional[str]:
    """Get the name of the currently active profile."""
    if ACTIVE_PROFILE_PATH.exists():
        try:
            return ACTIVE_PROFILE_PATH.read_text().strip()
        except OSError as e:
            # Log the specific error for debugging
            console.print(
                f"[yellow]Warning: Could not read active profile file: {e}[/yellow]"
            )
            raise DotzProfileError(f"Could not read active profile: {e}") from e
    return None


def delete_profile(name: str, quiet: bool = False) -> bool:
    """Delete a profile."""
    try:
        profiles_dir = get_profiles_dir()
        profile_path = profiles_dir / name

        if not profile_path.exists():
            if not quiet:
                console.print(f"[red]Profile '{name}' not found[/red]")
            return False

        # Check if it's the active profile
        active_profile = get_active_profile()
        if active_profile == name:
            if not quiet:
                console.print(f"[red]Cannot delete active profile '{name}'[/red]")
                console.print("[yellow]Switch to another profile first[/yellow]")
            return False

        shutil.rmtree(profile_path)

        if not quiet:
            console.print(f"[green]✓ Profile '{name}' deleted[/green]")

        return True

    except DotzProfileError:
        raise
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error deleting profile: {e}[/red]")
        raise DotzProfileError(f"Failed to delete profile: {e}") from e


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _create_repo_backup(backup_name: str, quiet: bool = False) -> bool:
    """Create a backup of the current repository state."""
    try:
        backup_dir = DOTZ_DIR / "backups" / "profiles"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = backup_dir / f"{backup_name}.tar.gz"

        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(WORK_TREE, arcname="repo")

        return True

    except Exception as e:
        if not quiet:
            console.print(f"[red]Error creating backup: {e}[/red]")
        return False


def _save_current_state_to_profile(profile_name: str, quiet: bool = False) -> bool:
    """Save the current repository state to a profile."""
    try:
        profiles_dir = get_profiles_dir()
        profile_path = profiles_dir / profile_name

        if not profile_path.exists():
            return True  # Profile doesn't exist, nothing to save

        profile_files_dir = profile_path / "files"
        profile_config_dir = profile_path / "config"

        # Clear existing profile content
        if profile_files_dir.exists():
            shutil.rmtree(profile_files_dir)
        if profile_config_dir.exists():
            shutil.rmtree(profile_config_dir)

        profile_files_dir.mkdir()
        profile_config_dir.mkdir()

        # Copy current repository files to profile
        repo = ensure_repo()
        tracked_files = repo.git.ls_files().splitlines()

        for file_rel in tracked_files:
            source_file = WORK_TREE / file_rel
            dest_file = profile_files_dir / file_rel
            if source_file.exists():
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)

        # Copy dotz configuration to profile
        config_file = DOTZ_DIR / "config.json"
        if config_file.exists():
            shutil.copy2(config_file, profile_config_dir / "config.json")

        tracked_dirs_file = DOTZ_DIR / "tracked_dirs.json"
        if tracked_dirs_file.exists():
            shutil.copy2(tracked_dirs_file, profile_config_dir / "tracked_dirs.json")

        return True

    except Exception as e:
        if not quiet:
            console.print(f"[red]Error saving current state: {e}[/red]")
        return False


def _apply_profile_state(profile_name: str, quiet: bool = False) -> bool:
    """Apply a profile's state to the current repository."""
    try:
        profiles_dir = get_profiles_dir()
        profile_path = profiles_dir / profile_name

        profile_files_dir = profile_path / "files"
        profile_config_dir = profile_path / "config"

        repo = ensure_repo()

        # Clear current repository (keep .git)
        for item in WORK_TREE.iterdir():
            if item.name != ".git":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        # Apply profile files
        if profile_files_dir.exists():
            for item in profile_files_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(profile_files_dir)
                    dest_path = WORK_TREE / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)

        # Apply profile configuration
        if profile_config_dir.exists():
            config_file = profile_config_dir / "config.json"
            if config_file.exists():
                shutil.copy2(config_file, DOTZ_DIR / "config.json")

            tracked_dirs_file = profile_config_dir / "tracked_dirs.json"
            if tracked_dirs_file.exists():
                shutil.copy2(tracked_dirs_file, DOTZ_DIR / "tracked_dirs.json")

        # Stage all changes
        repo.git.add("--all")

        # Commit profile switch
        try:
            repo.index.commit(f"Switch to profile '{profile_name}'")
        except Exception as e:
            # No changes to commit or other git error
            if not quiet:
                console.print(f"[yellow]Note: {e}[/yellow]")

        return True

    except Exception as e:
        if not quiet:
            console.print(f"[red]Error applying profile state: {e}[/red]")
        return False


def get_profile_info(name: str) -> Optional[ProfileMetadataDict]:
    """Get detailed information about a profile."""
    profiles_dir = get_profiles_dir()
    profile_path = profiles_dir / name

    if not profile_path.exists():
        return None

    metadata_file = profile_path / PROFILE_METADATA_FILE
    if not metadata_file.exists():
        return None

    try:
        with open(metadata_file) as f:
            metadata: Dict[str, Any] = json.load(f)

        # Add file count information
        profile_files_dir = profile_path / "files"
        if profile_files_dir.exists():
            file_count = len(list(profile_files_dir.rglob("*")))
            metadata["file_count"] = file_count
        else:
            metadata["file_count"] = 0

        # Add size information
        total_size = 0
        if profile_files_dir.exists():
            for file_path in profile_files_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        metadata["total_size"] = total_size

        # Check if active
        metadata["active"] = get_active_profile() == name

        return metadata

    except Exception:
        return None


def get_template_info(name: str) -> Optional[TemplateMetadataDict]:
    """Get detailed information about a template."""
    templates_dir = get_templates_dir()
    template_path = templates_dir / name

    if not template_path.exists():
        return None

    metadata_file = template_path / TEMPLATE_METADATA_FILE
    if not metadata_file.exists():
        return None

    try:
        with open(metadata_file) as f:
            metadata: Dict[str, Any] = json.load(f)

        # Add size information
        total_size = 0
        template_files_dir = template_path / "files"
        if template_files_dir.exists():
            for file_path in template_files_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        metadata["total_size"] = total_size

        return metadata

    except Exception:
        return None
