from flask import Blueprint, request, jsonify, g
import psycopg2
import bcrypt
import re
from ..utils.auth import generate_jwt_token, optional_token
from ..utils.constants import *

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email: str) -> bool:
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None

def is_valid_password(password: str) -> bool:
    """
    Validate password requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter  
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special

def is_valid_username(username: str) -> bool:
    from flask import current_app
    return len(username) <= current_app.config['USERNAME_LENGTH']

def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password

def verify_password(password, hashed_password):
    if isinstance(hashed_password, str):
        # Check if it's a hex string representation (starts with \x)
        if hashed_password.startswith('\\x'):
            # Remove the \x prefix and decode from hex
            hex_string = hashed_password[2:]
            hashed_password = bytes.fromhex(hex_string)
        else:
            hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)

@auth_bp.route("/handle_signup", methods=["POST"])
@optional_token
def handle_signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not email or not password or not username:
        return jsonify({"error": MISSING_SIGNUP_INFO}), 400

    email_valid = is_valid_email(email)
    password_valid = is_valid_password(password)
    username_valid = is_valid_username(username)

    if not email_valid or not password_valid or not username_valid:
        message = {
            "email": {
                "valid": bool(email_valid),
                "error": REQUIREMENT_EMAIL if not bool(email_valid) else "",
            },
            "username": {
                "valid": bool(username_valid),
                "error": REQUIREMENT_USERNAME if not bool(username_valid) else "",
            },
            "password": {
                "valid": bool(password_valid),
                "error": REQUIREMENT_PASSWORD if not bool(password_valid) else "",
            },
        }
        return jsonify({"error": MALFORMED_EMAIL_PASSWORD, "message": message}), 422

    g.cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = g.cursor.fetchone()
    if existing_user:
        return jsonify({"error": CONFLICT_EMAIL}), 409

    hashed_password = hash_password(password)

    try:
        g.cursor.execute(
            "INSERT INTO users (email, username, password) VALUES (%s, %s, %s) RETURNING id",
            (email, username, hashed_password),
        )
        user_id = g.cursor.fetchone()['id']
        g.db.commit()

        token = generate_jwt_token(user_id)

        return jsonify({
            "message": SUCCESS_SIGN_UP,
            "data": {"email": email, "username": username, "token": token},
        }), 201

    except psycopg2.Error as err:
        g.db.rollback()
        return jsonify({"error": INTERNAL_SERVER_ERROR}), 500

@auth_bp.route("/handle_login", methods=["POST"])
@optional_token
def handle_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": MISSING_LOGIN_INFO}), 400

    g.cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = g.cursor.fetchone()

    if user:
        stored_hashed_password = user.get("password")
        if verify_password(password, stored_hashed_password):
            user_id = user.get("id")
            token = generate_jwt_token(user_id)

            return jsonify({
                "message": SUCCESS_LOGIN,
                "data": {
                    "email": email,
                    "username": user.get("username"),
                    "token": token,
                },
            }), 200
        else:
            return jsonify({"error": INVALID_CREDENTIALS}), 401
    else:
        return jsonify({"error": INVALID_CREDENTIALS}), 401

@auth_bp.route("/handle_logout", methods=["POST"])
@optional_token
def handle_logout():
    # With stateless JWT, logout is handled client-side by discarding the token
    return jsonify({"message": SUCCESS_LOGOUT}), 200