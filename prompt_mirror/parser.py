"""
Parser for exported AI conversation files.
Supports ChatGPT, Claude, and Gemini export formats.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Handle zoneinfo for Python 3.9+
try:
    import zoneinfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False

# Maximum file size: 500MB
MAX_FILE_SIZE = 500 * 1024 * 1024

# Warning tracking
_parse_warnings: List[str] = []


def get_warnings() -> List[str]:
    """Get list of warnings from last parse operation."""
    return _parse_warnings.copy()


def clear_warnings():
    """Clear the warning list."""
    global _parse_warnings
    _parse_warnings = []


@dataclass
class Message:
    """Single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


@dataclass
class Conversation:
    """A single conversation thread."""
    id: str
    title: str
    messages: List[Message]
    create_time: Optional[datetime] = None
    source: str = "unknown"  # 'chatgpt', 'claude', 'gemini'


class ConversationParser:
    """Parse exported AI conversation files."""

    def parse(self, file_path: str, local_timezone: str = None) -> List[Conversation]:
        """
        Parse conversation file and return list of conversations.
        Auto-detects format based on file structure.
        
        Args:
            file_path: Path to JSON file or directory
            local_timezone: Optional timezone string (e.g., 'Asia/Jakarta').
                           If not set, timestamps remain in UTC.
        """
        # Clear warnings at public entry point only
        clear_warnings()
        return self._parse_impl(file_path, local_timezone)

    def _parse_impl(self, file_path: str, local_timezone: str = None) -> List[Conversation]:
        """
        Internal implementation of parse. Does not clear warnings.
        Called by parse() and _parse_directory().
        """
        global _parse_warnings
        
        # BUGFIX: Warn if timezone specified but zoneinfo not available (Python 3.8)
        if local_timezone and not HAS_ZONEINFO:
            _parse_warnings.append(
                f"Timezone '{local_timezone}' specified but zoneinfo not available. "
                "Timezone conversion requires Python 3.9+. "
                "Timestamps will remain in UTC. "
                "Install backports.zoneinfo for Python 3.8: pip install backports.zoneinfo"
            )
        
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.is_dir():
            return self._parse_directory(path, local_timezone)

        # File size validation
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size / (1024*1024):.1f}MB. "
                f"Maximum supported size is {MAX_FILE_SIZE / (1024*1024):.0f}MB. "
                f"Try splitting your export into smaller files."
            )

        # Try multiple encodings (UTF-8 first, then common alternatives)
        # BUGFIX: Removed 'cp1252' from list because 'latin-1' can decode ANY
        # byte sequence without raising UnicodeDecodeError. This means cp1252
        # was never actually reached. If latin-1 decoding succeeds but produces
        # garbage, json.load() will likely fail with JSONDecodeError anyway.
        encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16', 'latin-1']
        data = None
        last_error = None
        
        for encoding in encodings_to_try:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                break  # Success, exit loop
            except UnicodeDecodeError as e:
                last_error = e
                continue  # Try next encoding
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON file: {file_path}. Error: {e}")
        
        if data is None:
            raise ValueError(
                f"Could not read file {file_path} with any supported encoding. "
                f"Last error: {last_error}"
            )

        # Detect format
        if self._is_chatgpt_format(data):
            return self._parse_chatgpt(data, local_timezone)
        elif self._is_claude_format(data):
            return self._parse_claude(data, local_timezone)
        elif self._is_gemini_format(data):
            return self._parse_gemini(data, local_timezone)
        else:
            # Try generic format
            return self._parse_generic(data)

    def _parse_directory(self, dir_path: Path, local_timezone: str = None) -> List[Conversation]:
        """Parse all JSON files in a directory."""
        conversations = []

        for json_file in dir_path.glob("*.json"):
            try:
                # Use internal method to avoid clearing warnings for each file
                convs = self._parse_impl(str(json_file), local_timezone)
                conversations.extend(convs)
            except Exception as e:
                _parse_warnings.append(f"Could not parse {json_file.name}: {e}")

        return conversations

    def _is_chatgpt_format(self, data) -> bool:
        """Check if data matches ChatGPT export format."""
        # ChatGPT exports are dicts with 'mapping' key, or list of such dicts
        if isinstance(data, dict):
            return "mapping" in data
        if isinstance(data, list) and len(data) > 0:
            return isinstance(data[0], dict) and "mapping" in data[0]
        return False

    def _is_claude_format(self, data) -> bool:
        """Check if data matches Claude export format."""
        if isinstance(data, dict):
            # Must NOT have 'mapping' (ChatGPT)
            if "mapping" in data:
                return False
            if "conversations" in data or "messages" in data:
                # Check for Gemini patterns first (Gemini also has 'conversations' key)
                conv_list = data.get("conversations", data.get("messages", []))
                if isinstance(conv_list, list) and len(conv_list) > 0:
                    first_conv = conv_list[0] if isinstance(conv_list[0], dict) else {}
                    # Gemini has 'history' or 'parts' - reject these
                    if "history" in first_conv:
                        return False  # This is Gemini
                    # Claude has 'chat_messages' or 'uuid' field
                    if "chat_messages" in first_conv or "uuid" in first_conv:
                        return True
                    # Check for Claude message structure
                    msgs = first_conv.get("messages", first_conv.get("chat_messages", []))
                    if msgs and isinstance(msgs, list) and isinstance(msgs[0], dict):
                        # Claude uses 'sender', Gemini uses 'role'
                        if "sender" in msgs[0]:
                            return True
                        if "role" in msgs[0] and "parts" not in msgs[0]:
                            return True  # Has role but no parts = likely Claude
                # BUGFIX: Was returning True for empty/unmatched structures
                # Only return True if we have actual evidence of Claude format
                return False  # Don't claim Claude format for unknown structures
        return False

    def _is_gemini_format(self, data) -> bool:
        """Check if data matches Gemini export format."""
        # Gemini exports are typically lists with 'history' or 'conversation' keys
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict):
                return "conversation" in first or "history" in first
            return False
        if isinstance(data, dict):
            # Gemini dict format has 'conversations' with 'history' inside
            convs = data.get("conversations", [])
            if isinstance(convs, list) and len(convs) > 0:
                first = convs[0] if isinstance(convs[0], dict) else {}
                # Gemini has 'history' with 'parts' structure
                if "history" in first or "parts" in first:
                    return True
        return False

    def _parse_chatgpt(self, data: dict, local_timezone: str = None) -> List[Conversation]:
        """Parse ChatGPT export format.
        
        Args:
            data: Parsed JSON data
            local_timezone: Optional timezone to convert timestamps to
        """
        conversations = []
        skipped_messages = 0

        # ChatGPT exports can be a list or have conversations nested
        conv_list = data if isinstance(data, list) else [data]

        for conv_data in conv_list:
            if not conv_data:
                continue

            messages = []
            mapping = conv_data.get("mapping", {})

            # Parse messages from mapping
            for msg_id, msg_data in mapping.items():
                if not msg_data:
                    skipped_messages += 1
                    continue

                message_info = msg_data.get("message", {})
                if not message_info:
                    skipped_messages += 1
                    continue

                author = message_info.get("author")
                # Handle None author or non-dict author
                if not isinstance(author, dict):
                    skipped_messages += 1
                    continue
                role = author.get("role", "")
                if role not in ["user", "assistant"]:
                    skipped_messages += 1
                    continue

                # BUGFIX: content can be null in real ChatGPT exports
                # Use 'or {}' to handle None value, not just missing key
                content_info = message_info.get("content") or {}
                content_parts = content_info.get("parts", [])
                try:
                    content = " ".join(
                        part if isinstance(part, str) else part.get("text", "")
                        for part in content_parts
                    )
                except Exception:
                    content = ""
                    skipped_messages += 1

                create_time = None
                if message_info.get("create_time"):
                    try:
                        # ChatGPT uses Unix timestamp (UTC)
                        create_time = datetime.fromtimestamp(
                            message_info["create_time"], 
                            tz=timezone.utc
                        )
                        # Convert to local timezone if specified
                        if local_timezone and HAS_ZONEINFO:
                            tz = zoneinfo.ZoneInfo(local_timezone)
                            create_time = create_time.astimezone(tz)
                    except Exception:
                        pass

                messages.append(Message(
                    role=role,
                    content=content,
                    timestamp=create_time
                ))

            if messages:
                # Sort by timestamp (use max datetime for messages without timestamp)
                # We use a very old date in UTC to avoid naive/aware comparison issues
                _min_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
                messages.sort(key=lambda m: m.timestamp or _min_time)

                conversations.append(Conversation(
                    id=conv_data.get("id", "unknown"),
                    title=self._extract_title(conv_data) or "Untitled",
                    messages=messages,
                    create_time=messages[0].timestamp if messages else None,
                    source="chatgpt"
                ))

        if skipped_messages > 0:
            _parse_warnings.append(f"Skipped {skipped_messages} messages that couldn't be parsed from ChatGPT format")

        return conversations

    def _parse_claude(self, data: dict, local_timezone: str = None) -> List[Conversation]:
        """Parse Claude export format.
        
        Args:
            data: Parsed JSON data
            local_timezone: Optional timezone to convert timestamps to
        """
        conversations = []
        skipped_messages = 0

        conv_list = data.get("conversations", data.get("messages", []))
        if not isinstance(conv_list, list):
            conv_list = [conv_list]

        for i, conv_data in enumerate(conv_list):
            messages = []

            msg_list = conv_data.get("messages", conv_data.get("chat_messages", []))

            for msg_data in msg_list:
                role = msg_data.get("sender", msg_data.get("role", ""))
                # Normalize role
                if role in ["human", "user"]:
                    role = "user"
                elif role in ["assistant", "ai"]:
                    role = "assistant"

                if role not in ["user", "assistant"]:
                    skipped_messages += 1
                    continue

                content = msg_data.get("text", msg_data.get("content", ""))
                # BUGFIX: Claude API can return content as list of blocks
                # e.g., [{"type": "text", "text": "hello"}]
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    content = " ".join(text_parts)
                elif isinstance(content, dict):
                    # Claude API can return content as dict e.g. {"text": "hello"}
                    content = content.get("text", str(content))
                elif not isinstance(content, str):
                    content = str(content) if content else ""

                timestamp = None
                if msg_data.get("created_at"):
                    try:
                        # Claude uses ISO format with timezone
                        timestamp = datetime.fromisoformat(
                            msg_data["created_at"].replace("Z", "+00:00")
                        )
                        # Convert to local timezone if specified
                        if local_timezone and timestamp and HAS_ZONEINFO:
                            tz = zoneinfo.ZoneInfo(local_timezone)
                            timestamp = timestamp.astimezone(tz)
                    except Exception:
                        pass

                messages.append(Message(
                    role=role,
                    content=content,
                    timestamp=timestamp
                ))

            if messages:
                conversations.append(Conversation(
                    id=conv_data.get("id", conv_data.get("uuid", f"claude_{i}")),
                    title=conv_data.get("name", conv_data.get("title", "Untitled")),
                    messages=messages,
                    create_time=messages[0].timestamp if messages else None,
                    source="claude"
                ))

        if skipped_messages > 0:
            _parse_warnings.append(f"Skipped {skipped_messages} messages that couldn't be parsed from Claude format")

        return conversations

    def _parse_gemini(self, data: dict, local_timezone: str = None) -> List[Conversation]:
        """Parse Gemini export format.
        
        Args:
            data: Parsed JSON data
            local_timezone: Optional timezone to convert timestamps to (if available)
        """
        conversations = []
        skipped_messages = 0

        conv_list = data if isinstance(data, list) else data.get("conversations", [])

        for i, conv_data in enumerate(conv_list):
            messages = []

            history = conv_data.get("history", conv_data.get("conversation", []))

            for msg_data in history:
                if not isinstance(msg_data, dict):
                    skipped_messages += 1
                    continue
                role = msg_data.get("role", "")
                if role not in ["user", "model"]:
                    skipped_messages += 1
                    continue

                # Gemini uses "model" instead of "assistant"
                if role == "model":
                    role = "assistant"

                parts = msg_data.get("parts", [])
                content_parts = []
                for part in parts:
                    if isinstance(part, dict):
                        content_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        content_parts.append(part)
                    elif isinstance(part, (list, tuple)):
                        # Handle nested structures - extract text from nested
                        for subpart in part:
                            if isinstance(subpart, dict):
                                content_parts.append(subpart.get("text", ""))
                            elif isinstance(subpart, str):
                                content_parts.append(subpart)
                    else:
                        content_parts.append(str(part))
                content = " ".join(content_parts)

                messages.append(Message(
                    role=role,
                    content=content,
                    timestamp=None
                ))

            if messages:
                # Try to extract a meaningful title from first user message
                title = f"Gemini Chat {i + 1}"  # Default fallback
                for msg in messages:
                    if msg.role == "user" and msg.content.strip():
                        content = msg.content.strip()
                        if len(content) > 10:
                            # Use first 50 chars as title
                            title = content[:50] + "..." if len(content) > 50 else content
                        break
                
                conversations.append(Conversation(
                    id=conv_data.get("id", f"gemini_{i}"),
                    title=title,
                    messages=messages,
                    source="gemini"
                ))

        if skipped_messages > 0:
            _parse_warnings.append(f"Skipped {skipped_messages} messages that couldn't be parsed from Gemini format")

        return conversations

    def _parse_generic(self, data: dict) -> List[Conversation]:
        """Try to parse unknown format."""
        conversations = []

        # Try to find any list of messages
        if isinstance(data, list):
            messages = []
            for item in data:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    messages.append(Message(
                        role=item["role"],
                        content=item["content"],
                        timestamp=None
                    ))

            if messages:
                conversations.append(Conversation(
                    id="generic_1",
                    title="Imported Conversation",
                    messages=messages,
                    source="generic"
                ))

        return conversations

    def _extract_title(self, conv_data: dict) -> Optional[str]:
        """Extract conversation title from ChatGPT format."""
        # Try different possible locations
        # BUGFIX: title key can exist with None value in ChatGPT exports
        # Must check that title is actually a non-empty string before returning
        if conv_data.get("title"):
            return conv_data["title"]

        # Try to get from first user message
        mapping = conv_data.get("mapping", {})
        for msg_data in mapping.values():
            if not msg_data:
                continue
            # BUGFIX: message can be null (e.g. root node in ChatGPT exports)
            # dict.get("message", {}) returns None if key exists with value None
            # Must use `or {}` to handle explicit null, same pattern as content
            message = msg_data.get("message") or {}
            author = message.get("author")
            # Handle None author same as in _parse_chatgpt
            if not isinstance(author, dict):
                continue
            if author.get("role") == "user":
                # BUGFIX: content can be null (same as _parse_chatgpt line 253)
                # dict.get("content", {}) returns None if key exists with value None
                # Must use `or {}` to handle explicit null
                content_parts = (message.get("content") or {}).get("parts", [])
                # Safely get first element, handle empty list
                if content_parts:
                    content = content_parts[0]
                else:
                    continue
                if isinstance(content, str) and len(content) > 10:
                    # Use first 50 chars as title
                    return content[:50] + "..." if len(content) > 50 else content

        return None
