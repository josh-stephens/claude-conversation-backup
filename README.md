# Claude Conversation Backup System

A robust backup and conversion system for Claude Code conversations with Obsidian Vault integration.

## Features

- **Automated Backups**: Scheduled backups of all Claude conversations
- **Markdown Conversion**: Converts JSONL conversation logs to Obsidian-compatible Markdown
- **Device-Aware Organization**: Automatically organizes conversations by device and date
- **Rich Metadata**: Obsidian Bases properties for advanced querying
- **Error Prevention**: Built-in hooks and documentation to prevent common Windows/WSL issues
- **Multi-Device Support**: Device registration through dotfiles for consistent backups across machines
- **Email Notifications**: Monitoring alerts for backup failures

## Components

### Core Scripts
- `claude-to-markdown.py` - Python converter for JSONL to Markdown with Obsidian properties
- `backup-conversations-markdown.sh` - WSL backup script with Markdown conversion

### Documentation & Hooks
- `.claude/docs/windows-wsl-file-operations.md` - Comprehensive guide for Windows/WSL operations
- `.claude/hooks/post-tool-use.ps1` - Error detection hook with documentation reminders
- `CLAUDE.md` - Primary environment reference for Claude Code

## Installation

1. Clone this repository to your Windows home directory:
```bash
gh repo clone josh-stephens/claude-conversation-backup ~/bin
```

2. Ensure Python 3 is installed in WSL:
```bash
wsl -e which python3
```

3. Set up the backup directory:
```powershell
New-Item -Path "C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)" -ItemType Directory -Force
```

## Usage

### Manual Backup
Run from WSL:
```bash
~/bin/backup-conversations-markdown.sh
```

### View Converted Conversations
Conversations are saved as Markdown files in:
```
C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)\Devices\[DeviceName]\[YYYY]\[MM]\[DD]\
```

Each conversation includes:
- Obsidian Bases properties (device, platform, tags, tools used, etc.)
- Formatted conversation with timestamps
- Tool usage and results
- Automatic tagging based on content

## Obsidian Integration

The Markdown files are optimized for Obsidian's Bases feature (released August 2025):

### Properties Include
- `device`: Device that created the conversation
- `platform`: Windows/WSL/macOS
- `date`: Conversation date
- `project_path`: Original project directory
- `tools_used`: Array of Claude tools used
- `tags`: Auto-generated based on content
- `duration_minutes`: Conversation length
- `status`: completed/in_progress/completed_with_errors

### Example Query in Obsidian
Find all Python conversations with errors:
```
tags: python AND has_errors: true
```

## Configuration

### Backup Target
Default: `C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)`

To change, edit `claude-to-markdown.py`:
```python
config = {
    'backup_target': r'C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)',
    'device_name': None  # Auto-detect
}
```

### Email Notifications
Configure in backup script for monitoring alerts:
- Server: `se-ubuntu` (port 25, no auth)
- Sender: `claudeconvos@eusd.org`
- Recipient: `josh.stephens@gmail.com`

## Troubleshooting

### WSL EIO Errors
If you encounter "Input/output error":
1. Run `wsl --shutdown`
2. Wait 5 seconds
3. Clear any lock files: `wsl -e rm -f /home/josh/.claude.lock`
4. Retry the operation

### Conversion Failures
Check the backup log:
```powershell
Get-Content "C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)\backup.log" -Tail 50
```

### Missing Conversations
Verify source directory:
```bash
wsl -e find /home/josh/.claude/projects -name "*.jsonl" -type f | wc -l
```

## Development

### Adding Device Support
Devices are auto-detected using hostname and platform. To customize, modify `get_device_info()` in `claude-to-markdown.py`.

### Extending Metadata
Add new properties to the YAML frontmatter section in `convert_conversation()`.

### Custom Tags
Modify the `generate_tags()` function to add domain-specific tagging logic.

## Future Enhancements

- [ ] SMB share support for Tailscale network portability
- [ ] Real-time backup triggers
- [ ] Conversation search API
- [ ] Duplicate detection
- [ ] Incremental backups
- [ ] Web viewer interface

## License

MIT

## Author

Josh Stephens

---

*Part of the Claude Code ecosystem for enhanced AI conversation management*