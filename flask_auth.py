import base64
import json
from flask import request
from functools import wraps
import os

JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "").replace("\\n", "\n")
ALGORITHM = os.getenv("ALGORITHM", "RS256")

def get_current_user():
    """
    Function để lấy thông tin người dùng từ header X-User trong Flask
    Returns: dict - thông tin user hoặc None nếu không có
    """
    x_user = request.headers.get("x-user")
    if not x_user:
        return None
    
    try:
        decoded_user = base64.b64decode(x_user).decode("utf-8")
        user_data = json.loads(decoded_user)
        return user_data
    except Exception as e:
        print(f"Error decoding user data: {e}")
        return None

def require_auth(f):
    """
    Decorator để yêu cầu authentication cho Flask routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return {"error": "Unauthorized: Missing or invalid user data"}, 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_or_error():
    """
    Function để lấy thông tin user và raise error nếu không có
    Returns: dict - thông tin user
    Raises: Exception nếu không có user
    """
    user = get_current_user()
    if not user:
        raise Exception("Unauthorized: Missing or invalid user data")
    return user