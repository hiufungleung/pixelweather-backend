from flask import Blueprint, request, jsonify, g
import psycopg2
import bcrypt
from ..utils.auth import token_required
from ..utils.constants import *
from .auth_routes import is_valid_email, is_valid_username, is_valid_password, hash_password, verify_password

user_bp = Blueprint('user', __name__)

@user_bp.route("/handle_update_email", methods=["PATCH"])
@token_required
def handle_update_email():
    data = request.get_json()
    new_email = data.get("email")

    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not new_email:
        return jsonify({"error": MISSING_EMAIL}), 400

    if not is_valid_email(new_email):
        return jsonify({
            "error": MALFORMED_EMAIL,
            "message": {"email": {"valid": False, "error": REQUIREMENT_EMAIL}},
        }), 422

    g.cursor.execute("SELECT * FROM users WHERE email = %s", (new_email,))
    existing_user = g.cursor.fetchone()
    if existing_user:
        return jsonify({"error": CONFLICT_EMAIL}), 409

    try:
        g.cursor.execute(
            "UPDATE users SET email = %s WHERE id = %s", (new_email, user_id)
        )
        g.db.commit()

        return jsonify({
            "message": SUCCESS_EMAIL_CHANGED,
            "data": {"email": new_email},
        }), 200
    except psycopg2.Error as err:
        g.db.rollback()
        return jsonify({"error": INTERNAL_SERVER_ERROR}), 500
@user_bp.route("/handle_update_password", methods=["PATCH"])
@token_required
def handle_update_password():
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not current_password or not new_password:
        return jsonify({"error": MISSING_OLD_NEW_PASSWORD}), 400

    if not is_valid_password(current_password):
        return jsonify({
            "error": MALFORMED_PASSWORD,
            "message": {
                "password": {"valid": False, "error": REQUIREMENT_PASSWORD}
            },
        }), 422

    try:
        g.cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = g.cursor.fetchone()

        if not user or not verify_password(current_password, user.get("password")):
            return jsonify({"error": INCORRECT_PASSWORD}), 403

        hashed_password = hash_password(new_password)

        g.cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id)
        )
        g.db.commit()

        return jsonify({"message": SUCCESS_PASSWORD_CHANGED}), 200
    except psycopg2.Error as err:
        g.db.rollback()
        return jsonify({"error": INTERNAL_SERVER_ERROR}), 500
@user_bp.route("/handle_update_username", methods=["PATCH"])
@token_required
def handle_update_username():
    data = request.get_json()
    new_username = data.get("username")

    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not new_username:
        return jsonify({"error": MISSING_NEW_USERNAME}), 400

    if not is_valid_username(new_username):
        return jsonify({
            "error": MALFORMED_USERNAME,
            "message": {"username": False, "error": REQUIREMENT_USERNAME},
        }), 422

    try:
        g.cursor.execute(
            "UPDATE users SET username = %s WHERE id = %s", (new_username, user_id)
        )
        g.db.commit()

        return jsonify({
            "message": SUCCESS_USERNAME_CHANGED,
            "data": {"username": new_username},
        }), 200
    except psycopg2.Error as err:
        g.db.rollback()
        return jsonify({"error": INTERNAL_SERVER_ERROR}), 500
@user_bp.route("/handle_delete_account", methods=["DELETE"])
@token_required
def handle_delete_account():
    data = request.get_json()
    password = data.get("password")

    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not password:
        return jsonify({"error": MISSING_PASSWORD}), 400

    try:
        g.cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = g.cursor.fetchone()

        if not user or not verify_password(password, user.get("password")):
            return jsonify({"error": INCORRECT_PASSWORD}), 403

        g.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        g.db.commit()

        return jsonify({"message": SUCCESS_DATA_DELETED}), 200

    except psycopg2.Error as err:
        g.db.rollback()
        return jsonify({"error": INTERNAL_SERVER_ERROR}), 500
