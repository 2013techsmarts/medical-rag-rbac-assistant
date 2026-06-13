import hashlib

# Salt for demo hashing consistency
_SALT = "medibot_demo_salt_secure_2026"


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 and salt."""
    return hashlib.sha256((password + _SALT).encode()).hexdigest()


# Raw demo credentials defined in requirements
_RAW_USERS = {
    "dr.mehta": {"password": "doctor", "role": "doctor"},
    "nurse.priya": {"password": "nurse", "role": "nurse"},
    "billing.ravi": {"password": "billing_executive", "role": "billing_executive"},
    "tech.anand": {"password": "technician", "role": "technician"},
    "admin.sys": {"password": "admin", "role": "admin"},
}

# Hash passwords dynamically at module load time
USERS = {}
for username, info in _RAW_USERS.items():
    USERS[username] = {
        "hashed_password": _hash_password(info["password"]),
        "role": info["role"],
    }


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate a user against the demo store.
    
    Args:
        username: Provided username.
        password: Provided plaintext password.
        
    Returns:
        Dict with 'username' and 'role' if valid, else None.
    """
    user = USERS.get(username.lower().strip())
    if not user:
        return None

    if _hash_password(password) == user["hashed_password"]:
        return {"username": username, "role": user["role"]}
    return None
