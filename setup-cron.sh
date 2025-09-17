#!/bin/bash
# Setup cron job for Claude backup

# Create crontab entry
cat << 'EOF' | crontab -
# Claude Conversation Backup - Daily at 3 AM
0 3 * * * /home/josh/bin/backup-conversations-markdown.sh >> /home/josh/.claude-backup.log 2>&1
EOF

echo "Crontab installed successfully!"
echo "Current crontab:"
crontab -l