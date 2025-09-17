#!/bin/bash

# Claude Conversations Markdown Backup Script
# Simple, efficient backup with Markdown conversion for Obsidian

# Configuration
SOURCE_DIR="$HOME/.claude/projects"
DEST_BASE="/mnt/c/Users/josh/Documents/Mine/Claude Code Conversation Backups (Automated)"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="$DEST_BASE/backup_$DATE"
MARKDOWN_DIR="$DEST_BASE"
LOG_FILE="$DEST_BASE/backup.log"
CONVERTER_SCRIPT="/mnt/c/Users/josh/bin/claude-to-markdown-v3.py"

# Create destination directories
mkdir -p "$DEST_BASE"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start backup
log_message "Starting Claude conversations backup with Markdown conversion"
log_message "Source: $SOURCE_DIR"
log_message "Markdown output: $MARKDOWN_DIR"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    log_message "ERROR: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

# Count files and calculate size
FILE_COUNT=$(find "$SOURCE_DIR" -name "*.jsonl" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$SOURCE_DIR" 2>/dev/null | cut -f1 || echo "unknown")

log_message "Found $FILE_COUNT conversation files, total size: $TOTAL_SIZE"

# Check if Python script exists
if [ ! -f "$CONVERTER_SCRIPT" ]; then
    log_message "ERROR: Markdown converter script not found at $CONVERTER_SCRIPT"
    exit 1
fi

# Run conversion
log_message "Converting conversations to Markdown..."
python3 "$CONVERTER_SCRIPT" "$SOURCE_DIR" "$MARKDOWN_DIR" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log_message "Markdown conversion completed successfully"
else
    log_message "ERROR: Markdown conversion failed"
    # Send email notification for failure
    echo "Backup failed at $(date). Check $LOG_FILE for details." | mail -s "Claude Backup Failed" -r "claudeconvos@eusd.org" josh.stephens@gmail.com 2>/dev/null || true
    exit 1
fi

# Create backup summary
MARKDOWN_COUNT=$(find "$MARKDOWN_DIR" -name "*.md" 2>/dev/null | wc -l)

# Update tracking
echo "$(date): $FILE_COUNT files converted to $MARKDOWN_COUNT markdown files" > "$DEST_BASE/latest.txt"

log_message "Backup summary:"
log_message "- Source files: $FILE_COUNT"
log_message "- Markdown files: $MARKDOWN_COUNT"

# Force filesystem sync to prevent EIO issues
sync
sleep 1

log_message "Backup process completed successfully - filesystem synced"
log_message "----------------------------------------"