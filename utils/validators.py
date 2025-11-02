"""
Input Validators Module
Handles validation and sanitization of user inputs
"""

from typing import Tuple, Optional
import re
from utils.translations import t


def validate_user_input(user_input: str, language: str = "English") -> Tuple[bool, Optional[str]]:
    """
    Validate and sanitize user input
    
    Args:
        user_input: User's input string
        language: Current language for error messages
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check if empty
    if not user_input or not user_input.strip():
        return False, t("input_empty", language)
    
    # Check length
    if len(user_input) > 500:
        return False, t("input_too_long", language)
    
    # Check for SQL injection attempts
    dangerous_patterns = [
        r';--',           # SQL comment
        r'\/\*.*?\*\/',   # Multi-line comment
        r'\bDROP\b',      # DROP statement
        r'\bDELETE\b',    # DELETE statement
        r'\bINSERT\b',    # INSERT statement
        r'\bUPDATE\b',    # UPDATE statement
        r'\bEXEC\b',      # EXEC statement
        r'\bTRUNCATE\b',  # TRUNCATE statement
        r'<script',       # XSS attempt
        r'javascript:',   # JavaScript injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return False, t("input_invalid", language)
    
    # Check for excessive special characters (possible attack)
    special_char_count = sum(1 for c in user_input if not c.isalnum() and not c.isspace())
    if special_char_count > len(user_input) * 0.3:  # More than 30% special chars
        return False, t("input_invalid", language)
    
    return True, None


def sanitize_sql_output(sql_query: str) -> str:
    """
    Sanitize SQL query for safe display
    Remove potential harmful content before showing to user
    
    Args:
        sql_query: SQL query string
    
    Returns:
        Sanitized query string
    """
    if not sql_query:
        return ""
    
    # Remove comments
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
    
    # Remove extra whitespace
    sql_query = ' '.join(sql_query.split())
    
    return sql_query


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe for file operations
    
    Args:
        filename: Proposed filename
    
    Returns:
        True if safe, False otherwise
    """
    # Only allow alphanumeric, dash, underscore, and dot
    safe_pattern = r'^[a-zA-Z0-9_\-\.]+$'
    
    if not re.match(safe_pattern, filename):
        return False
    
    # Prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    return True


def normalize_search_term(term: str) -> str:
    """
    Normalize search term for database queries
    
    Args:
        term: Search term
    
    Returns:
        Normalized term
    """
    # Remove extra whitespace
    term = ' '.join(term.split())
    
    # Convert to lowercase for case-insensitive search
    term = term.lower()
    
    # Remove potentially dangerous characters
    term = re.sub(r'[;\'"\\]', '', term)
    
    return term.strip()
