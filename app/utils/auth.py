import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app, g
from ..models.database import get_db_connection, get_db_cursor, return_db_connection

def generate_jwt_token(user_id: int) -> str:
    """Generate a JWT token for a user"""
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=current_app.config['JWT_EXPIRATION_DAYS']),
        "iat": datetime.datetime.now(datetime.UTC)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")
    return token

def verify_jwt_token(token: str):
    """Verify a JWT token"""
    try:
        decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        # Handle the Bearer prefix
        if token.startswith("Bearer "):
            token = token[len("Bearer "):]

        decoded_token = verify_jwt_token(token)
        if not decoded_token:
            return jsonify({"error": "Token is invalid"}), 401

        # Store decoded token in g for use in the route
        g.decoded_token = decoded_token
        g.db = get_db_connection()
        g.cursor = get_db_cursor(g.db)
        
        return f(*args, **kwargs)
    return decorated

def optional_token(f):
    """Decorator for routes that optionally use tokens"""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.db = get_db_connection()
        g.cursor = get_db_cursor(g.db)
        return f(*args, **kwargs)
    return decorated