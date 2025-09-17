#!/usr/bin/env python3
"""
Claude Conversations to Markdown Converter v3
- True 1:1 mapping between sessions and Markdown files
- Updates existing files instead of creating duplicates
- Consistent file naming based on session ID
"""

import json
import os
import sys
import socket
import platform
from datetime import datetime
from pathlib import Path
import re
import hashlib

def get_device_info():
    """Get device identification information"""
    hostname = socket.gethostname()
    system = platform.system()

    # Check if running in WSL
    is_wsl = 'microsoft' in platform.uname().release.lower()

    if is_wsl:
        device_name = f"{hostname}-WSL"
        platform_name = "WSL/Linux"
    elif system == "Windows":
        device_name = hostname
        platform_name = "Windows"
    elif system == "Darwin":
        device_name = hostname
        platform_name = "macOS"
    else:
        device_name = hostname
        platform_name = system

    return device_name, platform_name

def clean_filename(text, max_length=80):
    """Clean text for use as filename"""
    # Remove or replace invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + '...'
    return cleaned

def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable format"""
    try:
        # Handle various timestamp formats
        if 'Z' in iso_timestamp:
            # UTC timestamp with Z suffix
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        elif '+' in iso_timestamp or iso_timestamp.count(':') > 2:
            # Already has timezone info
            dt = datetime.fromisoformat(iso_timestamp)
        else:
            # Naive datetime - assume local timezone
            dt = datetime.fromisoformat(iso_timestamp)

        # Remove timezone info for consistent comparison
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        return dt.strftime('%H:%M:%S'), dt.strftime('%Y-%m-%d'), dt
    except Exception as e:
        # Fallback: return current time if parsing fails
        now = datetime.now()
        return now.strftime('%H:%M:%S'), now.strftime('%Y-%m-%d'), now

def extract_content(message):
    """Extract readable content from message object"""
    if not message or 'content' not in message:
        return ""

    content = message['content']

    # Handle string content
    if isinstance(content, str):
        return content

    # Handle array content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'Unknown Tool')
                    tool_input = item.get('input', {})

                    parts.append(f"\n**[Tool: {tool_name}]**")

                    # Handle Bash commands specially
                    if tool_name == 'Bash' and 'command' in tool_input:
                        parts.append(f"```bash\n{tool_input['command']}\n```")
                        if 'description' in tool_input:
                            parts.append(f"*{tool_input['description']}*")
                    else:
                        # Handle other tools
                        for key, value in tool_input.items():
                            if key == 'file_path':
                                parts.append(f"File: `{value}`")
                            elif key == 'content' or key == 'old_string' or key == 'new_string':
                                # Truncate long content
                                if isinstance(value, str) and len(value) > 500:
                                    value = value[:500] + "...\n[truncated]"
                                parts.append(f"```\n{value}\n```")
                            else:
                                parts.append(f"{key}: {value}")

                elif item.get('type') == 'tool_result':
                    # Handle tool results
                    tool_name = item.get('tool_name', 'Tool')
                    result_content = item.get('content', '')

                    if isinstance(result_content, list) and result_content:
                        result_content = result_content[0].get('text', '') if isinstance(result_content[0], dict) else str(result_content[0])

                    parts.append(f"\n**[Result]**")
                    # Truncate very long results
                    if len(str(result_content)) > 1000:
                        result_content = str(result_content)[:1000] + "...\n[truncated]"
                    parts.append(f"```\n{result_content}\n```")

        return '\n'.join(parts)

    return str(content)

def extract_tools_used(lines):
    """Extract list of tools used in conversation"""
    tools = set()
    for line in lines:
        try:
            entry = json.loads(line)
            message = entry.get('message', {})
            if isinstance(message.get('content'), list):
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        tools.add(item.get('name', 'Unknown'))
        except:
            continue
    return sorted(list(tools))

def generate_tags(content, project_path):
    """Generate tags based on content and context"""
    tags = []

    # Add tags based on project path
    if 'wsl' in project_path.lower() or '/mnt/' in project_path:
        tags.append('wsl')
    if 'windows' in project_path.lower() or 'C:\\' in project_path:
        tags.append('windows')

    # Add tags based on content keywords
    content_lower = content.lower()
    keyword_tags = {
        'python': ['python', '.py', 'pip', 'django', 'flask'],
        'javascript': ['javascript', '.js', 'node', 'npm', 'react', 'vue'],
        'docker': ['docker', 'container', 'dockerfile'],
        'git': ['git ', 'commit', 'branch', 'merge'],
        'database': ['sql', 'database', 'postgres', 'mysql', 'mongodb'],
        'api': ['api', 'rest', 'graphql', 'endpoint'],
        'terminal': ['bash', 'shell', 'terminal', 'command'],
        'configuration': ['config', 'settings', '.env', 'yaml'],
    }

    for tag, keywords in keyword_tags.items():
        if any(keyword in content_lower for keyword in keywords):
            tags.append(tag)

    return tags

def decode_project_path(encoded_path):
    """Decode the project path from directory name"""
    if not encoded_path.startswith('-'):
        return encoded_path

    # Remove leading dash and replace dashes with slashes
    decoded = encoded_path[1:].replace('-', '/')

    # Special handling for Windows paths
    if decoded.startswith('mnt/c/'):
        # Convert WSL path to Windows path
        decoded = 'C:/' + decoded[6:]
    elif decoded.startswith('home/'):
        # Keep as Linux path
        decoded = '/' + decoded

    return decoded

def get_session_file_path(session_id, device_name, output_base_dir):
    """Get the consistent file path for a session"""
    # Use first 2 chars of session ID for folder organization
    if session_id.startswith('unknown_'):
        folder = 'unknown'
    else:
        folder = session_id[:2]

    # Create path: Devices/DeviceName/xx/session_id.md
    device_dir = output_base_dir / "Devices" / device_name / folder
    device_dir.mkdir(parents=True, exist_ok=True)

    return device_dir / f"{session_id}.md"

def read_existing_metadata(file_path):
    """Read metadata from existing Markdown file"""
    if not file_path.exists():
        return None

    metadata = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        in_frontmatter = False
        for line in f:
            if line.strip() == '---':
                if in_frontmatter:
                    break
                in_frontmatter = True
                continue

            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    return metadata

def convert_conversation(jsonl_file, output_base_dir, config):
    """Convert or update a JSONL conversation to/in Markdown"""
    try:
        device_name, platform_name = get_device_info()

        # Read conversation
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            return None

        # Parse metadata from first entry
        first_entry = json.loads(lines[0])
        last_entry = json.loads(lines[-1])

        session_id = first_entry.get('sessionId', 'unknown')

        # For unknown sessions, create stable ID from project path and first message
        if session_id == 'unknown':
            parent_dir = Path(jsonl_file).parent.name
            first_msg = ""
            for line in lines[:10]:  # Check first 10 lines for user message
                try:
                    entry = json.loads(line)
                    if entry.get('type') == 'user':
                        first_msg = str(entry.get('message', ''))[:100]
                        break
                except:
                    pass

            # Create hash from project directory and first message
            id_source = f"{parent_dir}:{first_msg}"
            session_id = f"unknown_{hashlib.md5(id_source.encode()).hexdigest()[:12]}"

        # Get consistent file path
        output_file = get_session_file_path(session_id, device_name, output_base_dir)

        # Read existing metadata if file exists
        existing_metadata = read_existing_metadata(output_file) if output_file.exists() else None

        # Parse conversation metadata
        cwd = first_entry.get('cwd', 'unknown')
        first_timestamp = first_entry.get('timestamp', '')
        first_time_str, first_date_str, first_dt = format_timestamp(first_timestamp)

        last_timestamp = last_entry.get('timestamp', '')
        last_time_str, last_date_str, last_dt = format_timestamp(last_timestamp)

        # Calculate conversation duration
        duration_minutes = int((last_dt - first_dt).total_seconds() / 60)

        # Extract project path from the directory structure
        parent_dir = Path(jsonl_file).parent.name
        actual_project_path = decode_project_path(parent_dir)

        # Use the actual project path from directory, fallback to cwd if needed
        if actual_project_path and actual_project_path != 'unknown':
            project_path = actual_project_path
        else:
            project_path = cwd

        project_name = Path(project_path).name if project_path != 'unknown' else 'general'

        # Get first user message for title
        conversation_title = f"Session {session_id[:8]}"
        first_message = ""
        for line in lines:
            try:
                entry = json.loads(line)
                if entry.get('type') == 'user' and entry.get('message'):
                    content = extract_content(entry['message'])
                    if content:
                        first_message = content[:100]
                        # Create a clean title from first message
                        conversation_title = clean_filename(first_message, 50)
                        break
            except:
                continue

        # Extract tools used
        tools_used = extract_tools_used(lines)

        # Check for errors in conversation
        has_errors = any('error' in line.lower() or 'failed' in line.lower() for line in lines)

        # Build full content for tag generation
        full_content = ""
        for line in lines:
            try:
                entry = json.loads(line)
                if 'message' in entry:
                    full_content += extract_content(entry['message']) + "\n"
            except:
                continue

        # Generate tags
        tags = generate_tags(full_content, project_path)

        # Determine status
        status = "active" if duration_minutes < 5 else "completed"
        if has_errors:
            status = "completed_with_errors"

        # Preserve first_seen from existing file, or use current first timestamp
        if existing_metadata and 'first_seen' in existing_metadata:
            first_seen = existing_metadata['first_seen']
        else:
            first_seen = first_timestamp

        # Build Markdown content with Obsidian properties
        md_content = []
        md_content.append("---")
        md_content.append("# Obsidian Bases Properties")
        md_content.append(f"device: {device_name}")
        md_content.append(f"platform: {platform_name}")
        md_content.append(f"user: {first_entry.get('userType', 'unknown')}")
        md_content.append(f"first_seen: {first_seen}")
        md_content.append(f"last_updated: {last_timestamp}")
        md_content.append(f"date: {first_date_str}")
        md_content.append(f"session_id: {session_id}")
        md_content.append(f"project_path: {project_path}")
        md_content.append(f"project_name: {project_name}")
        md_content.append(f"conversation_title: {conversation_title}")
        md_content.append(f"message_count: {len(lines)}")
        md_content.append(f"tools_used: {json.dumps(tools_used)}")
        md_content.append(f"tags: {json.dumps(tags)}")
        md_content.append(f"duration_minutes: {duration_minutes}")
        md_content.append(f"model: {first_entry.get('model', 'unknown')}")
        md_content.append(f"status: {status}")
        md_content.append(f"has_errors: {str(has_errors).lower()}")
        md_content.append("---")
        md_content.append("")
        md_content.append(f"# {conversation_title}")
        md_content.append("")
        md_content.append(f"**Session:** `{session_id}`")
        md_content.append(f"**Device:** {device_name} | **Platform:** {platform_name}")
        md_content.append(f"**Started:** {first_date_str} {first_time_str} | **Updated:** {last_date_str} {last_time_str}")
        md_content.append(f"**Project:** `{project_path}`")
        md_content.append(f"**Duration:** {duration_minutes} minutes | **Messages:** {len(lines)}")
        md_content.append("")
        md_content.append("---")
        md_content.append("")

        # Convert messages
        for line in lines:
            try:
                entry = json.loads(line)
                msg_type = entry.get('type', 'unknown')
                timestamp = entry.get('timestamp', '')
                time_str, date_str, _ = format_timestamp(timestamp)
                message = entry.get('message', {})

                if msg_type == 'user':
                    md_content.append(f"## 🧑 User [{date_str} {time_str}]")
                    content = extract_content(message)
                    md_content.append(content)
                    md_content.append("")

                elif msg_type == 'assistant':
                    md_content.append(f"## 🤖 Assistant [{date_str} {time_str}]")
                    content = extract_content(message)
                    md_content.append(content)
                    md_content.append("")

                elif msg_type == 'tool_result':
                    # Tool results are usually part of the flow
                    md_content.append(f"### Tool Result [{time_str}]")
                    if 'content' in entry:
                        md_content.append(f"```\n{entry['content']}\n```")
                    md_content.append("")

            except json.JSONDecodeError as e:
                print(f"Error parsing line: {e}")
                continue

        # Write file
        action = "Updated" if output_file.exists() else "Created"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))

        print(f"[{action}] {session_id}: {conversation_title}")
        return session_id, action

    except Exception as e:
        print(f"[ERROR] Converting {jsonl_file}: {e}")
        import traceback
        traceback.print_exc()
        return None, "Error"

def main():
    """Main conversion function"""
    # Default configuration
    config = {
        'backup_target': r'C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)',
        'device_name': None  # Auto-detect if not specified
    }

    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python3 claude-to-markdown-v3.py <source_dir> [output_dir]")
        print("  source_dir: Directory containing .claude/projects with JSONL files")
        print("  output_dir: Optional output directory (defaults to config)")
        sys.exit(1)

    source_dir = Path(sys.argv[1])

    # Determine output directory
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path(config['backup_target'])

    if not source_dir.exists():
        print(f"[ERROR] Source directory does not exist: {source_dir}")
        sys.exit(1)

    # Create output directory structure
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all JSONL files
    jsonl_files = list(source_dir.rglob("*.jsonl"))
    print(f"Found {len(jsonl_files)} conversation files to process")

    if not jsonl_files:
        print("No JSONL files found!")
        return

    # Convert files
    created = 0
    updated = 0
    failed = 0

    for i, jsonl_file in enumerate(jsonl_files, 1):
        print(f"[{i}/{len(jsonl_files)}] Processing {jsonl_file.name}...")
        result = convert_conversation(jsonl_file, output_dir, config)
        if result:
            session_id, action = result
            if action == "Created":
                created += 1
            elif action == "Updated":
                updated += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*60)
    print(f"Conversion Complete!")
    print(f"[CREATED] New files: {created}")
    print(f"[UPDATED] Existing files: {updated}")
    if failed > 0:
        print(f"[FAILED] {failed} files")
    print(f"[OUTPUT] Directory: {output_dir}")
    print("="*60)

if __name__ == "__main__":
    main()