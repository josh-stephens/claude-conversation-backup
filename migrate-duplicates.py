#!/usr/bin/env python3
"""
Migration script to clean up duplicate Markdown files and reorganize to v3 structure
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict
import hashlib

def extract_session_id(filepath):
    """Extract session ID from Markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('session_id:'):
                return line.split(':', 1)[1].strip()
    return None

def extract_metadata(filepath):
    """Extract key metadata from Markdown file"""
    metadata = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        in_frontmatter = False
        for line in f:
            if line.strip() == '---':
                if in_frontmatter:
                    break
                in_frontmatter = True
                continue

            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                if key in ['message_count', 'timestamp', 'first_seen', 'last_updated']:
                    metadata[key] = value.strip()

    # Parse message count as integer
    if 'message_count' in metadata:
        try:
            metadata['message_count'] = int(metadata['message_count'])
        except:
            metadata['message_count'] = 0

    return metadata

def get_new_path(session_id, device_name, base_dir):
    """Get the v3 path for a session"""
    if session_id.startswith('unknown'):
        folder = 'unknown'
    else:
        folder = session_id[:2]

    return base_dir / "Devices" / device_name / folder / f"{session_id}.md"

def main():
    """Migrate old structure to v3"""
    vault_dir = Path(r"C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)")

    # Find all existing Markdown files in old structure
    old_devices_dir = vault_dir / "Devices"
    if not old_devices_dir.exists():
        print("No existing Devices folder found")
        return

    # Collect all MD files
    all_files = list(old_devices_dir.rglob("*.md"))
    print(f"Found {len(all_files)} Markdown files to process")

    # Group by session ID
    sessions = defaultdict(list)
    for filepath in all_files:
        session_id = extract_session_id(filepath)
        if session_id:
            sessions[session_id].append(filepath)
        else:
            print(f"[WARNING] No session ID found in: {filepath.name}")

    # Process duplicates
    print(f"\nFound {len(sessions)} unique sessions")
    duplicates_removed = 0
    files_migrated = 0

    # Create backup directory for old structure
    backup_dir = vault_dir / "OLD_STRUCTURE_BACKUP"
    backup_dir.mkdir(exist_ok=True)

    for session_id, files in sessions.items():
        if len(files) > 1:
            # Multiple files for same session - keep the most complete one
            best_file = None
            best_count = 0

            for f in files:
                metadata = extract_metadata(f)
                msg_count = metadata.get('message_count', 0)
                if msg_count > best_count:
                    best_count = msg_count
                    best_file = f

            print(f"\nSession {session_id[:8]}... has {len(files)} duplicates")
            print(f"  Keeping: {best_file.name} ({best_count} messages)")

            # Get device name from path
            device_name = best_file.parts[-5]  # Devices/DeviceName/YYYY/MM/DD/file.md

            # Create new path
            new_path = get_new_path(session_id, device_name, vault_dir)
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy best file to new location
            shutil.copy2(best_file, new_path)
            print(f"  Migrated to: {new_path.relative_to(vault_dir)}")
            files_migrated += 1

            # Move all old files to backup
            for f in files:
                backup_path = backup_dir / f.relative_to(old_devices_dir)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(backup_path))
                if f != best_file:
                    duplicates_removed += 1
                    print(f"  Backed up duplicate: {f.name}")

        else:
            # Single file - just reorganize
            f = files[0]
            device_name = f.parts[-5]  # Devices/DeviceName/YYYY/MM/DD/file.md

            # Create new path
            new_path = get_new_path(session_id, device_name, vault_dir)
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Move to new location
            shutil.copy2(f, new_path)

            # Backup old file
            backup_path = backup_dir / f.relative_to(old_devices_dir)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(backup_path))

            files_migrated += 1

    # Clean up empty directories in old structure
    for root, dirs, files in os.walk(old_devices_dir, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except:
                pass

    print("\n" + "="*60)
    print("Migration Complete!")
    print(f"Files migrated: {files_migrated}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Old structure backed up to: {backup_dir}")
    print("="*60)

if __name__ == "__main__":
    main()