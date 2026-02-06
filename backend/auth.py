import json
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import hashlib

# --- CONFIGURATION ---
SECRET_KEY = "jarvis_secret_key_change_this"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
USERS_FILE = "users.json"

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- DATABASE HELPERS ---

def _read_users_db():
    """Reads the JSON file containing users."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_users_db(data):
    """Writes data to the JSON user file."""
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(username: str):
    """Retrieves a user dictionary by username."""
    db = _read_users_db()
    return db.get(username)

# --- PASSWORD LOGIC ---

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- USER CREATION (This is where your error was) ---

def create_user_in_db(username, password):
    """Creates a new user and initializes their storage."""
    # 1. Check if user exists (Uses the function defined above)
    if get_user(username):
        return False
    
    # 2. Hash password and save
    hashed_pw = get_password_hash(password)
    db = _read_users_db()
    db[username] = {
        "username": username,
        "hashed_password": hashed_pw
    }
    _write_users_db(db)
    
    # 3. Initialize Memory/Storage Folders for this user
    try:
        # Import inside function to avoid circular import issues
        from brain.memory_manager import init_db
        init_db(username)
    except ImportError:
        print(f"⚠️ Warning: Could not initialize DB for {username}. Check imports.")
    except Exception as e:
        print(f"⚠️ Error initializing DB: {e}")
        
    return True

# --- TOKEN LOGIC ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates the token and returns the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user