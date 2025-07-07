# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :x:                |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in loom, please report it by emailing **salemmoustafa442@gmail.com**.

**Please do not report security vulnerabilities through public GitHub issues.**

When reporting a vulnerability, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (if you have them)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Timeline**: Varies by severity, but critical issues will be prioritized

## Security Considerations

loom manages sensitive configuration files that may contain:
- API keys and tokens
- Database credentials
- SSH keys
- Personal configuration data

### Best Practices for Users

1. **Review files before adding**: Always review what files you're adding to loom
2. **Use private repositories**: If syncing to a remote, ensure your repository is private
3. **Rotate sensitive credentials**: Regularly rotate any credentials stored in config files
4. **Limit repository access**: Only grant access to trusted collaborators
5. **Use environment variables**: Consider using environment variables for sensitive values instead of storing them in config files

### Security Features

- loom operates locally and only syncs when explicitly requested
- No automatic cloud syncing without user consent
- Git-based versioning provides audit trail of all changes
- Symlink-based approach preserves file permissions

## Scope

This security policy applies to the loom project hosted at https://github.com/tTrmc/loom.

Thank you for helping keep loom secure!
