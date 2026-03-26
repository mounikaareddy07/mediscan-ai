"""
MediScan AI - Authentication Utilities
Password hashing, token generation, and validation helpers.
"""

import hashlib
import secrets
import re


def hash_password(password):
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"


def verify_password(password, stored_hash):
    """Verify a password against its stored hash."""
    try:
        salt, pwd_hash = stored_hash.split(':')
        return hashlib.sha256((salt + password).encode()).hexdigest() == pwd_hash
    except (ValueError, AttributeError):
        return False


def generate_token():
    """Generate a secure session token."""
    return secrets.token_hex(32)


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """Validate password strength (minimum 6 characters)."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, "Password is valid."


def validate_signup(full_name, username, email, password, confirm_password):
    """Validate all signup fields."""
    errors = []

    if not full_name or len(full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters.")

    if not username or len(username.strip()) < 3:
        errors.append("Username must be at least 3 characters.")

    if not validate_email(email):
        errors.append("Please enter a valid email address.")

    valid, msg = validate_password(password)
    if not valid:
        errors.append(msg)

    if password != confirm_password:
        errors.append("Passwords do not match.")

    return errors
