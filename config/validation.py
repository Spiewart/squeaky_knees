"""Input validation and sanitization utilities."""

import html
import json
import re
from typing import Any

# Safe HTML tags for rich text comments
SAFE_TAGS = {
    "p", "br", "strong", "em", "u", "a", "ul", "ol", "li", "blockquote", "code", "pre", "h1", "h2", "h3", "h4", "h5", "h6"
}

# Maximum lengths for common fields
MAX_COMMENT_LENGTH = 5000
MAX_USERNAME_LENGTH = 150
MAX_EMAIL_LENGTH = 254


def sanitize_html(html_content: str) -> str:
    """Sanitize HTML to prevent XSS attacks by removing dangerous tags.

    Args:
        html_content: Raw HTML string

    Returns:
        Sanitized HTML string with dangerous tags removed
    """
    if not isinstance(html_content, str):
        return ""

    # Remove script tags and content
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    # Remove event handlers
    sanitized = re.sub(r'\s+on\w+\s*=\s*["\']?[^"\'>\s]+["\']?', '', sanitized, flags=re.IGNORECASE)

    # Remove iframe tags
    sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)

    # Remove style tags
    sanitized = re.sub(r'<style[^>]*>.*?</style>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)

    return sanitized


def validate_comment_length(text_blocks: list) -> tuple[bool, str]:
    """Validate comment length by summing text content.

    Args:
        text_blocks: List of StreamField block dicts

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(text_blocks, list):
        return False, "Invalid comment format"

    total_length = 0
    for block in text_blocks:
        if isinstance(block, dict) and "value" in block:
            value = block["value"]
            # For rich_text blocks, strip HTML tags for length calculation
            if block.get("type") == "rich_text" and isinstance(value, str):
                clean_text = re.sub(r'<[^>]+>', '', value)
                total_length += len(clean_text)
            # For code blocks, use the content directly
            elif block.get("type") == "code" and isinstance(value, dict):
                total_length += len(value.get("content") or value.get("code", ""))

    if total_length == 0:
        return False, "Comment cannot be empty"

    if total_length > MAX_COMMENT_LENGTH:
        return False, f"Comment exceeds maximum length of {MAX_COMMENT_LENGTH} characters"

    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format.

    Args:
        username: Username string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(username, str):
        return False, "Username must be a string"

    username = username.strip()

    if not username:
        return False, "Username cannot be empty"

    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username exceeds maximum length of {MAX_USERNAME_LENGTH}"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    # Only allow alphanumeric, underscore, hyphen
    if not all(c.isalnum() or c in "_-" for c in username):
        return False, "Username can only contain letters, numbers, underscore, and hyphen"

    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format and length.

    Args:
        email: Email string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(email, str):
        return False, "Email must be a string"

    email = email.strip().lower()

    if not email:
        return False, "Email cannot be empty"

    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email exceeds maximum length of {MAX_EMAIL_LENGTH}"

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[1]:
        return False, "Invalid email format"

    # Prevent domain spoofing
    if email.count("@") != 1:
        return False, "Invalid email format"

    local, domain = email.rsplit("@", 1)

    if not local or not domain:
        return False, "Invalid email format"

    if len(local) > 64:  # RFC 5321
        return False, "Email local part exceeds maximum length"

    return True, ""


def sanitize_streamfield_blocks(blocks: list) -> tuple[list, list]:
    """Sanitize StreamField blocks for XSS attacks.

    Args:
        blocks: List of StreamField block dicts

    Returns:
        Tuple of (sanitized_blocks, error_messages)
    """
    if not isinstance(blocks, list):
        return [], ["Invalid block format"]

    sanitized = []
    errors = []

    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            errors.append(f"Block {i} is not a dictionary")
            continue

        block_type = block.get("type")
        value = block.get("value")

        if block_type == "rich_text":
            if not isinstance(value, str):
                errors.append(f"Block {i} rich_text value must be string")
                continue

            sanitized_html = sanitize_html(value)
            sanitized.append({
                "type": "rich_text",
                "value": sanitized_html
            })

        elif block_type == "code":
            if not isinstance(value, dict):
                errors.append(f"Block {i} code value must be dict")
                continue

            content = value.get("content") or value.get("code", "")
            language = value.get("language", "")

            # Validate content is string and not too long
            if not isinstance(content, str):
                errors.append(f"Block {i} code content must be string")
                continue

            if len(content) > 10000:  # Max code block size
                errors.append(f"Block {i} code content exceeds 10000 characters")
                continue

            sanitized.append({
                "type": "code",
                "value": {
                    "code": content,
                    "content": content,
                    "language": language if isinstance(language, str) else "",
                }
            })

        else:
            errors.append(f"Block {i} has unknown type: {block_type}")

    return sanitized, errors
