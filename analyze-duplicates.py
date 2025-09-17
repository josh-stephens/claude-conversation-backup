#!/usr/bin/env python3
"""Analyze duplicate Markdown conversations and check for missing project paths"""

import os
import re
from pathlib import Path
from collections import defaultdict
import hashlib

def get_file_hash(filepath):
    """Get MD5 hash of file content"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def extract_session_id(filepath):
    """Extract session ID from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'session_id:\s*([a-f0-9-]+)', content)
        if match:
            return match.group(1)
    return None

def extract_project_path(filepath):
    """Extract project path from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'project_path:\s*(.+)', content)
        if match:
            return match.group(1).strip()
    return None

def main():
    vault_dir = Path(r"C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)\Devices")

    # Find all markdown files
    md_files = list(vault_dir.rglob("*.md"))
    print(f"Found {len(md_files)} total Markdown files\n")

    # Group by session ID
    sessions = defaultdict(list)
    for filepath in md_files:
        session_id = extract_session_id(filepath)
        if session_id:
            sessions[session_id].append(filepath)

    # Find duplicates (same session ID)
    duplicates = {sid: files for sid, files in sessions.items() if len(files) > 1}

    if duplicates:
        print(f"Found {len(duplicates)} sessions with duplicates:\n")
        for session_id, files in list(duplicates.items())[:5]:  # Show first 5
            print(f"Session {session_id[:8]}... has {len(files)} copies:")
            for f in files:
                project = extract_project_path(f) or "NO PROJECT PATH"
                print(f"  - {f.name}")
                print(f"    Project: {project}")
            print()

    # Check for missing project paths
    missing_project = []
    for filepath in md_files:
        project = extract_project_path(filepath)
        if not project or project == "unknown":
            missing_project.append(filepath)

    if missing_project:
        print(f"\nFiles missing project path: {len(missing_project)}")
        for f in missing_project[:5]:
            print(f"  - {f.name}")

    # Group by file hash to find exact duplicates
    hashes = defaultdict(list)
    for filepath in md_files:
        file_hash = get_file_hash(filepath)
        hashes[file_hash].append(filepath)

    exact_dupes = {h: files for h, files in hashes.items() if len(files) > 1}
    if exact_dupes:
        print(f"\n{len(exact_dupes)} groups of EXACT duplicate files (same content):")
        for hash_val, files in list(exact_dupes.items())[:3]:
            print(f"  Group with {len(files)} identical files:")
            for f in files:
                print(f"    - {f.parent.name}/{f.name}")

if __name__ == "__main__":
    main()