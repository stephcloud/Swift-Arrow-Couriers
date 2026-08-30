import bcrypt
import json
import secrets
import time

CREDENTIALS_FILE = "staff_credentials.json"
TOKEN_LIFETIME_SECONDS = 300

ACTIVE_TOKENS = {}


def load_staff():
    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)


def check_credentials(username, password):
    """Check a plain-text password against the stored hash. Returns True/False"""
    staff = load_staff()
    record = staff.get(username)
    if record is None:
        return False
    password_bytes = password.encode("utf-8")
    stored_hash = record["password_hash"].encode("utf-8")
    return bcrypt.checkpw(password_bytes, stored_hash)


def get_position(username):
    staff = load_staff()
    record = staff.get(username)
    if record is None:
        return None
    return record["position"]


def issue_token(username):
    """Create a new unguessable token for a signed-in user"""
    token = secrets.token_hex(16)
    ACTIVE_TOKENS[token] = {
        "username": username,
        "position": get_position(username),
        "issued_at": time.time(),
    }
    return token


def validate_token(token):
    """Return the user info for a token, or None if it's invalid or expired."""
    info = ACTIVE_TOKENS.get(token)
    if info is None:
        return None
    age = time.time() - info["issued_at"]
    if age > TOKEN_LIFETIME_SECONDS:
        del ACTIVE_TOKENS[token]
        return None
    return info


def revoke_token(token):
    """Destroy a token (used for signing out)"""
    if token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[token]


def is_station_master(user_info):
    return user_info["position"] == "Station Master"
