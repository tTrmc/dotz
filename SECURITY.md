# Security Policy

## Table of Contents

* [Supported Versions](#supported-versions)
* [Reporting a Vulnerability](#reporting-a-vulnerability)
* [Response Timeline](#response-timeline)
* [Security Considerations](#security-considerations)
* [Best Practices for Users](#best-practices-for-users)
* [Security Features](#security-features)

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :x:                |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in dotz, please report it by emailing [salemmoustafa442@gmail.com](mailto:salemmoustafa442@gmail.com).

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

* A clear description of the vulnerability
* Detailed steps to reproduce the issue
* Potential impact and affected components
* Any suggested fixes or mitigations (if you have them)
* Your contact information for follow-up questions

### Confidentiality

* I will acknowledge receipt of your vulnerability report
* I will work with you to understand and validate the issue
* I will keep you informed of the progress toward a fix
* I will credit you in the security advisory (unless you prefer to remain anonymous)

## Response Timeline

* **Acknowledgment**: Within 48 hours of receiving the report
* **Initial Assessment**: Within 1 week of acknowledgment
* **Fix Development**: Timeline varies by severity
  * Critical vulnerabilities: Immediate priority
  * High severity: Within 2 weeks
  * Medium/Low severity: Next regular release cycle
* **Public Disclosure**: After fix is available and users have time to update

## Security Considerations

dotz manages sensitive configuration files that may contain:

* API keys and authentication tokens
* Database credentials and connection strings
* SSH keys and certificates
* Personal configuration data and file paths
* Application secrets and environment variables

### Threat Model

**Potential risks include:**

* **Credential exposure**: Sensitive data in configuration files
* **Unauthorized access**: If remote repositories are compromised
* **Data leakage**: Accidental public repository exposure
* **Local file access**: Unauthorized local system access
* **Supply chain**: Dependencies with vulnerabilities

## Best Practices for Users

### Repository Security

1. **Use private repositories**: Always use private Git repositories for dotfiles
2. **Limit repository access**: Only grant access to trusted collaborators
3. **Review repository permissions**: Regularly audit who has access
4. **Enable two-factor authentication**: Secure your Git hosting accounts

### File Management

1. **Review files before adding**: Always review what files you're adding to dotz
2. **Use .gitignore patterns**: Exclude sensitive files using dotz's pattern system
3. **Rotate sensitive credentials**: Regularly rotate any credentials stored in config files
4. **Audit tracked files**: Periodically review what files are being tracked

### Environment Security

1. **Use environment variables**: Consider environment variables for sensitive values instead of config files
2. **Secure local environment**: Ensure your local development environment is secure
3. **Regular updates**: Keep dotz and its dependencies updated
4. **Backup encryption**: Consider encrypting sensitive backup files

### Examples of Files to Exclude

```bash
# Add patterns to exclude sensitive files
dotz config add-pattern "*.key" --type exclude
dotz config add-pattern "*_rsa" --type exclude
dotz config add-pattern "*.pem" --type exclude
dotz config add-pattern "*password*" --type exclude
dotz config add-pattern "*secret*" --type exclude
```

## Security Features

### Built-in Protections

* **Local operation**: dotz operates locally and only syncs when explicitly requested
* **No automatic cloud syncing**: No data is sent to external services without user consent
* **Git-based versioning**: Complete audit trail of all changes
* **Symlink-based approach**: Preserves original file permissions and ownership
* **Configurable patterns**: Flexible include/exclude system for sensitive files

### Security-First Design

* **Minimal network access**: Only communicates with Git repositories you configure
* **No telemetry**: No usage data or analytics collection
* **Transparent operations**: All actions are visible and under user control
* **Standard tools**: Built on well-established Git and Python ecosystems

### Dependency Security

* **Minimal dependencies**: Only essential, well-maintained packages
* **Regular updates**: Dependencies are monitored and updated regularly
* **Security scanning**: Automated dependency vulnerability scanning
* **Pinned versions**: Specific dependency versions for reproducible builds

## Scope

This security policy applies to:

* The dotz project hosted at <https://github.com/tTrmc/dotz>
* The dotz package distributed via PyPI
* Official documentation and examples
* Related tooling and scripts in the repository

This policy does not cover:

* Third-party integrations or extensions
* User-specific configuration or dotfiles
* Git hosting providers (GitHub, GitLab, etc.)
* Dependencies' security issues (reported to respective maintainers)

## Security Updates

Security updates are distributed through:

* **GitHub Releases**: Tagged releases with security fixes
* **PyPI Updates**: Updated package versions
* **Security Advisories**: GitHub security advisories for critical issues
* **Release Notes**: Detailed changelog with security-related changes

## Contact

For security-related questions or concerns:

* **Email**: [salemmoustafa442@gmail.com](mailto:salemmoustafa442@gmail.com) (for security issues only)
* **GitHub Issues**: For general security questions (non-sensitive)
* **GitHub Security**: For coordinated disclosure

Thank you for helping keep dotz secure!
