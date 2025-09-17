#!/bin/bash
cat > /home/josh/bin/backup-conversations-markdown.sh << 'EOFSCRIPT'
#!/bin/bash

# Claude Conversations Markdown Backup Script
SOURCE_DIR="$HOME/.claude/projects"
DEST_BASE="/mnt/c/Users/josh/Documents/Mine/Claude Code Conversation Backups (Automated)"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
MARKDOWN_DIR="$DEST_BASE"
LOG_FILE="$DEST_BASE/backup.log"
CONVERTER_SCRIPT="/mnt/c/Users/josh/bin/claude-to-markdown.py"

mkdir -p "$DEST_BASE"

log_message() {
    echo "[$(date '%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "Starting Claude conversations backup with Markdown conversion"
log_message "Source: $SOURCE_DIR"

if [ ! -d "$SOURCE_DIR" ]; then
    log_message "ERROR: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

FILE_COUNT=$(find "$SOURCE_DIR" -name "*.jsonl" 2>/dev/null | wc -l)
log_message "Found $FILE_COUNT conversation files"

if [ ! -f "$CONVERTER_SCRIPT" ]; then
    log_message "ERROR: Converter script not found"
    exit 1
fi

log_message "Converting to Markdown..."
python3 "$CONVERTER_SCRIPT" "$SOURCE_DIR" "$MARKDOWN_DIR" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log_message "Conversion completed successfully"
else
    log_message "ERROR: Conversion failed"
    exit 1
fi

sync
sleep 1

log_message "Backup completed - filesystem synced"
log_message "----------------------------------------"
EOFSCRIPT

chmod +x /home/josh/bin/backup-conversations-markdown.sh
echo "Backup script created successfully"