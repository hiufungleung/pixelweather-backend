from flask import Blueprint, request, jsonify, g
import psycopg2
import datetime
from ..utils.auth import token_required
from ..utils.constants import *

user_data_bp = Blueprint('user_data', __name__)

def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02}'

def format_time(time_obj):
    """Format datetime.time object to HH:MM:SS string"""
    if hasattr(time_obj, 'strftime'):
        return time_obj.strftime('%H:%M:%S')
    else:
        # If it's already a string, return as-is
        return str(time_obj)

# User Saved Suburbs
@user_data_bp.route("/user_saved_suburb", methods=["GET"])
@token_required
def get_user_saved_suburbs():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        g.cursor.execute("""
            SELECT uss.id, uss.suburb_id, uss.label, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_saved_suburb uss
            JOIN suburbs s ON uss.suburb_id = s.id
            WHERE uss.user_id = %s
        """, (user_id,))
        
        saved_suburbs = g.cursor.fetchall()

        result = []
        for suburb in saved_suburbs:
            result.append({
                'id': suburb['id'],
                'suburb_id': suburb['suburb_id'],
                'label': suburb['label'],
                'suburb_name': suburb['suburb_name'],
                'post_code': suburb['postcode'],
                'latitude': float(suburb['latitude']),
                'longitude': float(suburb['longitude']),
                'state_code': suburb['state_code']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_saved_suburb", methods=["POST"])
@token_required
def add_user_saved_suburb():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    label = data.get("label")
    suburb_id = data.get("suburb_id")

    if not label or not suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE user_id = %s AND (label = %s OR suburb_id = %s)",
            (user_id, label, suburb_id),
        )
        existing = g.cursor.fetchone()
        if existing:
            if existing['label'] == label:
                return jsonify({"error": CONFLICT_SAVED_LABEL}), 409
            else:
                return jsonify({"error": CONFLICT_SAVED_SUBURB}), 409

        g.cursor.execute(
            "INSERT INTO user_saved_suburb (user_id, suburb_id, label) VALUES (%s, %s, %s) RETURNING id",
            (user_id, suburb_id, label),
        )
        new_id = g.cursor.fetchone()['id']
        g.db.commit()

        g.cursor.execute("""
            SELECT uss.id, uss.suburb_id, uss.label, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_saved_suburb uss
            JOIN suburbs s ON uss.suburb_id = s.id
            WHERE uss.id = %s AND uss.user_id = %s
        """, (new_id, user_id))
        saved_suburb = g.cursor.fetchone()

        result = {
            'id': saved_suburb['id'],
            'suburb_id': saved_suburb['suburb_id'],
            'label': saved_suburb['label'],
            'suburb_name': saved_suburb['suburb_name'],
            'post_code': saved_suburb['postcode'],
            'latitude': float(saved_suburb['latitude']),
            'longitude': float(saved_suburb['longitude']),
            'state_code': saved_suburb['state_code']
        }

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': result
        }), 201

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_saved_suburb", methods=["PUT"])
@token_required
def update_user_saved_suburb():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    saved_suburb_id = data.get("id")
    new_suburb_id = data.get("suburb_id")
    new_label = data.get("label")

    if not saved_suburb_id or not new_suburb_id or not new_label:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (new_suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE id = %s AND user_id = %s",
            (saved_suburb_id, user_id),
        )
        existing = g.cursor.fetchone()
        if not existing:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE user_id = %s AND (label = %s OR suburb_id = %s) AND id != %s",
            (user_id, new_label, new_suburb_id, saved_suburb_id),
        )
        conflict = g.cursor.fetchone()
        if conflict:
            if conflict['label'] == new_label:
                return jsonify({"error": CONFLICT_SAVED_LABEL}), 409
            else:
                return jsonify({"error": CONFLICT_SAVED_SUBURB}), 409

        g.cursor.execute(
            "UPDATE user_saved_suburb SET suburb_id = %s, label = %s WHERE id = %s AND user_id = %s",
            (new_suburb_id, new_label, saved_suburb_id, user_id),
        )
        g.db.commit()

        g.cursor.execute("""
            SELECT uss.id, uss.suburb_id, uss.label, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_saved_suburb uss
            JOIN suburbs s ON uss.suburb_id = s.id
            WHERE uss.id = %s AND uss.user_id = %s
        """, (saved_suburb_id, user_id))
        updated_suburb = g.cursor.fetchone()

        result = {
            'id': updated_suburb['id'],
            'suburb_id': updated_suburb['suburb_id'],
            'label': updated_suburb['label'],
            'suburb_name': updated_suburb['suburb_name'],
            'post_code': updated_suburb['postcode'],
            'latitude': float(updated_suburb['latitude']),
            'longitude': float(updated_suburb['longitude']),
            'state_code': updated_suburb['state_code']
        }

        return jsonify({
            'message': SUCCESS_DATA_UPDATED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_saved_suburb", methods=["DELETE"])
@token_required
def delete_user_saved_suburb():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    saved_suburb_id = data.get("id")

    if not saved_suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE id = %s AND user_id = %s",
            (saved_suburb_id, user_id),
        )
        existing = g.cursor.fetchone()
        if not existing:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "DELETE FROM user_saved_suburb WHERE id = %s AND user_id = %s",
            (saved_suburb_id, user_id),
        )
        g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_DELETED,
            'data': {'id': saved_suburb_id}
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
# User Alert Weather
@user_data_bp.route("/user_alert_weather", methods=["GET"])
@token_required
def get_user_alert_weathers():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        g.cursor.execute("""
            SELECT uaw.id, uaw.weather_id, wc.category, w.weather, w.weather_code
            FROM user_alert_weather uaw
            JOIN weathers w ON uaw.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE uaw.user_id = %s
        """, (user_id,))
        
        alert_weathers = g.cursor.fetchall()

        result = []
        for weather in alert_weathers:
            result.append({
                'id': weather['id'],
                'weather_id': weather['weather_id'],
                'category': weather['category'],
                'weather': weather['weather'],
                'weather_code': weather['weather_code']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
def batch_delete_user_alert_weather(user_id, weather_id):
    if weather_id not in WEATHER_ONE_TO_N:
        return False

    weather_ids = WEATHER_ONE_TO_N[weather_id]
    try:
        placeholders = ', '.join(['%s'] * len(weather_ids))
        g.cursor.execute(f"""
            DELETE FROM user_alert_weather
            WHERE user_id = %s AND weather_id IN ({placeholders})
        """, (user_id, *weather_ids))
        g.db.commit()
        return True
    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error in batch delete: {err}")
        return False

@user_data_bp.route("/user_alert_weather", methods=["POST"])
@token_required
def add_user_alert_weather():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    weather_id = data.get("weather_id")

    if not weather_id or weather_id not in WEATHER_ONE_TO_N:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        weather_ids = WEATHER_ONE_TO_N[weather_id]
        placeholders = ', '.join(['%s'] * len(weather_ids))
        g.cursor.execute(f"""
            SELECT weather_id FROM user_alert_weather
            WHERE user_id = %s AND weather_id IN ({placeholders})
        """, (user_id, *weather_ids))
        existing = g.cursor.fetchall()
        if existing:
            return jsonify({"error": "User has already saved this weather alert"}), 409

        for w_id in weather_ids:
            g.cursor.execute(
                "INSERT INTO user_alert_weather (user_id, weather_id) VALUES (%s, %s)",
                (user_id, w_id)
            )
        g.db.commit()

        g.cursor.execute("""
            SELECT uaw.id, uaw.weather_id, wc.category, w.weather, w.weather_code
            FROM user_alert_weather uaw
            JOIN weathers w ON uaw.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE uaw.user_id = %s AND uaw.weather_id = %s
        """, (user_id, weather_id))
        
        new_alert_weather = g.cursor.fetchone()

        result = {
            'id': new_alert_weather['id'],
            'weather_id': new_alert_weather['weather_id'],
            'category': new_alert_weather['category'],
            'weather': new_alert_weather['weather'],
            'weather_code': new_alert_weather['weather_code']
        }

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': result
        }), 201

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_alert_weather", methods=["PUT"])
@token_required
def update_user_alert_weather():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    alert_id = data.get("id")
    new_weather_id = data.get("weather_id")

    if not alert_id or new_weather_id is None or new_weather_id not in WEATHER_ONE_TO_N:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("""
            SELECT weather_id FROM user_alert_weather
            WHERE id = %s AND user_id = %s
        """, (alert_id, user_id))
        existing_alert = g.cursor.fetchone()
        if not existing_alert:
            return jsonify({"error": NOT_EXIST_FK}), 422

        old_weather_id = existing_alert['weather_id']
        batch_delete_user_alert_weather(user_id, old_weather_id)

        weather_ids = WEATHER_ONE_TO_N[new_weather_id]
        for w_id in weather_ids:
            g.cursor.execute(
                "INSERT INTO user_alert_weather (user_id, weather_id) VALUES (%s, %s)",
                (user_id, w_id)
            )
        g.db.commit()

        g.cursor.execute("""
            SELECT uaw.id, uaw.weather_id, wc.category, w.weather, w.weather_code
            FROM user_alert_weather uaw
            JOIN weathers w ON uaw.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE uaw.user_id = %s AND uaw.weather_id = %s
        """, (user_id, new_weather_id))
        
        updated_alert_weather = g.cursor.fetchone()

        result = {
            'id': updated_alert_weather['id'],
            'weather_id': updated_alert_weather['weather_id'],
            'category': updated_alert_weather['category'],
            'weather': updated_alert_weather['weather'],
            'weather_code': updated_alert_weather['weather_code']
        }

        return jsonify({
            'message': SUCCESS_DATA_UPDATED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_alert_weather", methods=["DELETE"])
@token_required
def delete_user_alert_weather():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    alert_id = data.get("id")

    if not alert_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("""
            SELECT weather_id FROM user_alert_weather
            WHERE id = %s AND user_id = %s
        """, (alert_id, user_id))
        existing_alert = g.cursor.fetchone()
        if not existing_alert:
            return jsonify({"error": NOT_EXIST_FK}), 422

        weather_id = existing_alert['weather_id']

        if batch_delete_user_alert_weather(user_id, weather_id):
            return jsonify({
                'message': SUCCESS_DATA_DELETED,
                'data': {
                    'id': alert_id
                }
            }), 200
        else:
            return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
# User Alert Suburbs
@user_data_bp.route("/user_alert_suburb", methods=["GET"])
@token_required
def get_user_alert_suburbs():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        g.cursor.execute("""
            SELECT uas.id, uas.suburb_id, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_alert_suburb uas
            JOIN suburbs s ON uas.suburb_id = s.id
            WHERE uas.user_id = %s
        """, (user_id,))
        
        alert_suburbs = g.cursor.fetchall()

        result = []
        for suburb in alert_suburbs:
            result.append({
                'id': suburb['id'],
                'suburb_id': suburb['suburb_id'],
                'suburb_name': suburb['suburb_name'],
                'post_code': suburb['postcode'],
                'latitude': float(suburb['latitude']),
                'longitude': float(suburb['longitude']),
                'state_code': suburb['state_code']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_alert_suburb", methods=["POST"])
@token_required
def add_user_alert_suburb():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    suburb_id = data.get("suburb_id")

    if not suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE user_id = %s AND suburb_id = %s",
            (user_id, suburb_id),
        )
        existing = g.cursor.fetchone()
        if existing:
            return jsonify({"error": "User has already set this alert suburb"}), 409

        g.cursor.execute(
            "INSERT INTO user_alert_suburb (user_id, suburb_id) VALUES (%s, %s) RETURNING id",
            (user_id, suburb_id),
        )
        new_id = g.cursor.fetchone()['id']
        g.db.commit()

        g.cursor.execute("""
            SELECT uas.id, uas.suburb_id, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_alert_suburb uas
            JOIN suburbs s ON uas.suburb_id = s.id
            WHERE uas.id = %s AND uas.user_id = %s
        """, (new_id, user_id))
        alert_suburb = g.cursor.fetchone()

        result = {
            'id': alert_suburb['id'],
            'suburb_id': alert_suburb['suburb_id'],
            'suburb_name': alert_suburb['suburb_name'],
            'post_code': alert_suburb['postcode'],
            'latitude': float(alert_suburb['latitude']),
            'longitude': float(alert_suburb['longitude']),
            'state_code': alert_suburb['state_code']
        }

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': result
        }), 201

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_alert_suburb", methods=["PUT"])
@token_required
def update_user_alert_suburb():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    alert_id = data.get("id")
    new_suburb_id = data.get("suburb_id")

    if not alert_id or not new_suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (new_suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE id = %s AND user_id = %s",
            (alert_id, user_id),
        )
        existing = g.cursor.fetchone()
        if not existing:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE user_id = %s AND suburb_id = %s AND id != %s",
            (user_id, new_suburb_id, alert_id),
        )
        conflict = g.cursor.fetchone()
        if conflict:
            return jsonify({"error": "User has already set this alert suburb"}), 409

        g.cursor.execute(
            "UPDATE user_alert_suburb SET suburb_id = %s WHERE id = %s AND user_id = %s",
            (new_suburb_id, alert_id, user_id),
        )
        g.db.commit()

        g.cursor.execute("""
            SELECT uas.id, uas.suburb_id, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_alert_suburb uas
            JOIN suburbs s ON uas.suburb_id = s.id
            WHERE uas.id = %s AND uas.user_id = %s
        """, (alert_id, user_id))
        updated_suburb = g.cursor.fetchone()

        result = {
            'id': updated_suburb['id'],
            'suburb_id': updated_suburb['suburb_id'],
            'suburb_name': updated_suburb['suburb_name'],
            'post_code': updated_suburb['postcode'],
            'latitude': float(updated_suburb['latitude']),
            'longitude': float(updated_suburb['longitude']),
            'state_code': updated_suburb['state_code']
        }

        return jsonify({
            'message': SUCCESS_DATA_UPDATED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_alert_suburb", methods=["DELETE"])
@token_required
def delete_user_alert_suburb():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    alert_id = data.get("id")

    if not alert_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE id = %s AND user_id = %s",
            (alert_id, user_id),
        )
        existing = g.cursor.fetchone()
        if not existing:
            return jsonify({"error": NOT_EXIST_FK}), 422

        g.cursor.execute(
            "DELETE FROM user_alert_suburb WHERE id = %s AND user_id = %s",
            (alert_id, user_id),
        )
        g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_DELETED,
            'data': {'id': alert_id}
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
# User Alert Time
@user_data_bp.route("/user_alert_time", methods=["GET"])
@token_required
def get_user_alert_times():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        g.cursor.execute("""
            SELECT id, start_time, end_time, is_active
            FROM user_alert_time
            WHERE user_id = %s
        """, (user_id,))
        
        alert_times = g.cursor.fetchall()

        result = []
        for time in alert_times:
            start_time = format_time(time['start_time'])
            end_time = format_time(time['end_time'])
            result.append({
                'id': time['id'],
                'start_time': start_time,
                'end_time': end_time,
                'is_active': bool(time['is_active'])
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@user_data_bp.route("/user_alert_time", methods=["POST"])
@token_required
def add_user_alert_time():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    is_active = data.get("is_active")

    if not start_time or not end_time or is_active is None:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        start_time_obj = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
        end_time_obj = datetime.datetime.strptime(end_time, "%H:%M:%S").time()

        if start_time_obj >= end_time_obj:
            return jsonify({"error": "Invalid time range: start_time cannot be later than end_time"}), 422

        g.cursor.execute("""
            SELECT * FROM user_alert_time
            WHERE user_id = %s AND start_time = %s AND end_time = %s
        """, (user_id, start_time, end_time))
        
        existing = g.cursor.fetchone()
        if existing:
            return jsonify({"error": "User has already saved an alert time for this time range"}), 409

        g.cursor.execute("""
            INSERT INTO user_alert_time (user_id, start_time, end_time, is_active)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (user_id, start_time, end_time, is_active))
        
        new_id = g.cursor.fetchone()['id']
        g.db.commit()

        g.cursor.execute("""
            SELECT id, start_time, end_time, is_active
            FROM user_alert_time
            WHERE id = %s
        """, (new_id,))
        
        new_alert_time = g.cursor.fetchone()

        start_time = format_time(new_alert_time['start_time'])
        end_time = format_time(new_alert_time['end_time'])
        result = {
            'id': new_alert_time['id'],
            'start_time': start_time,
            'end_time': end_time,
            'is_active': bool(new_alert_time['is_active'])
        }

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': result
        }), 201

    except ValueError:
        return jsonify({"error": "Invalid time format. Use HH:MM:SS"}), 422
    except psycopg2.Error as err:
        g.db.rollback()
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
