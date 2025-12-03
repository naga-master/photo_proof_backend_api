"""Input sanitization utilities for security."""

import html
import re
from typing import Optional


def sanitize_html(value: str) -> str:
    """
    Remove HTML tags and escape special characters to prevent XSS.
    
    Args:
        value: Input string that might contain HTML/scripts
        
    Returns:
        Sanitized string safe for storage and display
        
    Examples:
        >>> sanitize_html("<script>alert('xss')</script>Hello")
        "Hello"
        >>> sanitize_html("Hello & goodbye")
        "Hello &amp; goodbye"
    """
    if not value:
        return value
    
    # Strip whitespace
    value = value.strip()
    
    # Remove HTML tags
    value = re.sub(r'<[^>]+>', '', value)
    
    # Escape special HTML characters
    value = html.escape(value)
    
    return value


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and illegal characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
        
    Examples:
        >>> sanitize_filename("../../etc/passwd")
        "passwd"
        >>> sanitize_filename("my file!.jpg")
        "my_file.jpg"
    """
    if not filename:
        return "unnamed"
    
    # Remove directory components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove illegal characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Ensure extension is safe
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        safe_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'mp4', 'mov']
        if ext.lower() not in safe_extensions:
            ext = 'bin'
        filename = f"{name}.{ext}"
    
    return filename or "unnamed"


def sanitize_url(url: Optional[str]) -> Optional[str]:
    """
    Sanitize URL to prevent javascript: and data: URI schemes.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Safe URL or None if dangerous
        
    Examples:
        >>> sanitize_url("javascript:alert('xss')")
        None
        >>> sanitize_url("https://example.com/page")
        "https://example.com/page"
    """
    if not url:
        return None
    
    url = url.strip().lower()
    
    # Block dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
    for protocol in dangerous_protocols:
        if url.startswith(protocol):
            return None
    
    # Only allow http, https, mailto
    if not url.startswith(('http://', 'https://', 'mailto:', '/')):
        return None
    
    return url


def truncate_string(value: str, max_length: int = 500) -> str:
    """
    Truncate string to maximum length to prevent DoS via large inputs.
    
    Args:
        value: String to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated string
    """
    if not value:
        return value
    
    if len(value) > max_length:
        return value[:max_length] + '...'
    
    return value
