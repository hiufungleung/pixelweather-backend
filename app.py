import os

from flask import Flask, request, render_template, jsonify, g
import mysql.connector
import re
from constants import *
import jwt
import datetime
import bcrypt
import json
import firebase_admin
from firebase_admin import credentials, messaging
import atexit
import requests
from mysql.connector import pooling
import pytz

app = Flask(__name__)

brisbane_tz = pytz.timezone('Australia/Brisbane')
SECRET_KEY = "YAKINIKU_DECO7381"
OPEN_WEATHER_API_KEY = "9480d17e216cfcf5b44da6050c7286a4"
GEOAPIFY_API_KEY = '2fb86e8ed34d45129f34c3fab949ecd4'

db_config = {'host': "149.28.188.65", 'user': "yakiniku", 'password': "30624700", 'database': "pixel_weather"}
connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=32, **db_config)


def get_db_connection():
    if 'db' not in g:
        g.db = connection_pool.get_connection()
    return g.db

cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)


NO_TOKEN_NEEDED_APIs = [
    "index",
    "handle_signup",
    "handle_login",
    "get_suburbs",
    "get_weathers",
    "get_filtered_posts",
]

TOKENS = {}


def save_token_store():
    """Development only"""
    with open("tokens.json", "w") as f:
        json.dump(TOKENS, f)


def load_token_store():
    """Development only"""
    global TOKENS
    try:
        with open("tokens.json", "r") as f:
            TOKENS = json.load(f)
    except FileNotFoundError:
        TOKENS = {}


# Helper function to generate JWT token
def generate_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(days=TOKEN_VALID_DURATION),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


# Helper function to verify JWT token
def verify_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_whitelisted(token) -> bool:
    # return r.get(token) is not None
    return token in TOKENS


def is_valid_username(username: str) -> bool:
    return len(username) <= USERNAME_LENGTH


def is_valid_email(email: str) -> bool:
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None


def is_valid_password(password: str) -> bool:
    return True


# Helper function to hash a password
def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password


def verify_password(password, hashed_password):
    """
    Helper function to check if the password matches the hash
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_suburb_id_from_geolocation(latitude: str, longitude: str) -> int | None:
    url = f"https://api.geoapify.com/v1/geocode/reverse?lat={latitude}&lon={longitude}&apiKey={GEOAPIFY_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("features"):
            properties = data["features"][0].get("properties", {})
            country = properties.get("country")
            suburb_name = properties.get("suburb", "Suburb not found")
            postcode = properties.get("postcode", "Postcode not found")
            state_code = properties.get("state_code", "State code not found")
        else:
            return None
    
    except requests.exceptions.RequestException:
        return None
    
    if country != 'Australia' or state_code != 'QLD':
        return None
    
    # avoid SQL injection syntax
    g.cursor.execute("SELECT * FROM suburbs WHERE postcode = %s", (postcode,))
    suburbs = g.cursor.fetchall()

    suburb_id = None
    if len(suburbs) > 1:
        for suburb in suburbs:
            if suburb['suburb_name'] == suburb_name:
                suburb_id = suburb['suburb_id']
                break
    if suburb_id is None:
        suburb_id = suburbs[0].get('id')
    return suburb_id

def get_current_weather(latitude: str, longitude: str) -> int | None:
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&appid={OPEN_WEATHER_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('current'):
            weather_code = data.get('current').get('weather')[0].get('id')
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None

    # avoid SQL injection syntax
    g.cursor.execute("SELECT * FROM weathers WHERE weather_code = %s", (weather_code,))
    weather_id = g.cursor.fetchone().get('id')
    return weather_id

@app.before_request
def before_request():
    if request.path.startswith('/static'):
        return
    if request.endpoint not in NO_TOKEN_NEEDED_APIs:
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": MISSING_TOKEN}), 400

        # Handle the Bearer prefix
        if token.startswith("Bearer "):
            token = token[len("Bearer ") :]

        if not is_token_whitelisted(token):
            return jsonify({"error": INVALID_TOKEN}), 401
        decoded_token = verify_token(token)
        if not decoded_token:
            return jsonify({"error": INVALID_TOKEN}), 401

        # Save the processed token, used for the real request function
        g.token = token
        g.decoded_token = decoded_token
    g.db = get_db_connection()
    g.cursor = g.db.cursor(dictionary=True)


@app.after_request
def after_request(response):
    save_token_store()
    return response


@app.errorhandler(500)
def internal_error(error):
    message = INTERNAL_SERVER_ERROR
    if os.getenv("FLASK_ENV") == "development":
        message += " " + str(error)
    return jsonify({"error": message}), 500


@app.teardown_request
def teardown_request(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/handle_signup", methods=["POST"])
def handle_signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    # Check if key is missing
    if not email or not password or not username:
        return jsonify({"error": MISSING_SIGNUP_INFO}), 400

    # Check if email, username or password is valid
    email_valid = is_valid_email(email)
    password_valid = is_valid_password(password)
    username_valid = len(username) <= USERNAME_LENGTH

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

    # avoid SQL injection syntax
    g.cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = g.cursor.fetchone()
    if existing_user:
        return jsonify({"error": CONFLICT_EMAIL}), 409

    # Hash password for security concerns
    hashed_password = hash_password(password)

    # Try to insert
    try:
        # avoid SQL injection syntax
        g.cursor.execute(
            "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)",
            (
                email,
                username,
                hashed_password,
            ),
        )
        g.db.commit()

        user_id = g.cursor.lastrowid
        token = generate_token(user_id)

        # Development only
        TOKENS[token] = user_id

        return (
            jsonify(
                {
                    "message": SUCCESS_SIGN_UP,
                    "data": {"email": email, "username": username, "token": token},
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        raise err


@app.route("/handle_login", methods=["POST"])
def handle_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": MISSING_LOGIN_INFO}), 400

    
    # avoid SQL injection syntax
    g.cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = g.cursor.fetchone()

    if user:
        stored_hashed_password = user.get("password")
        if verify_password(password, stored_hashed_password):
            user_id = user.get("id")
            token = generate_token(user_id)

            # Development only
            TOKENS[token] = user_id

            return (
                jsonify(
                    {
                        "message": SUCCESS_LOGIN,
                        "data": {
                            "email": email,
                            "username": user.get("username"),
                            "token": token,
                        },
                    }
                ),
                200,
            )
        else:
            # wrong password
            return jsonify({"error": INVALID_CREDENTIALS}), 401
    else:
        # No such user
        return jsonify({"error": INVALID_CREDENTIALS}), 401


@app.route("/handle_logout", methods=["POST"])
def handle_logout():
    token = g.token

    # Delete token from the whitelist
    # r.delete(token)
    # Development only
    del TOKENS[token]
    return jsonify({"message": SUCCESS_LOGOUT}), 200


@app.route("/handle_update_email", methods=["PATCH"])
def handle_update_email():
    data = request.get_json()
    new_email = data.get("email")

    # Get token from @app.before_request
    token = g.token
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not new_email:
        return jsonify({"error": MISSING_EMAIL}), 400

    if not is_valid_email(new_email):
        return (
            jsonify(
                {
                    "error": MALFORMED_EMAIL,
                    "message": {"email": {"valid": False, "error": REQUIREMENT_EMAIL}},
                }
            ),
            422,
        )

    # avoid SQL injection syntax
    g.cursor.execute("SELECT * FROM users WHERE email = %s", (new_email,))
    existing_user = g.cursor.fetchone()
    if existing_user:
        return jsonify({"error": CONFLICT_EMAIL}), 409

    try:
        # avoid SQL injection syntax
        g.cursor.execute(
            "UPDATE users SET email = %s WHERE id = %s", (new_email, user_id)
        )
        g.db.commit()

        return (
            jsonify(
                {
                    "message": SUCCESS_EMAIL_CHANGED,
                    "data": {"email": new_email},
                }
            ),
            200,
        )
    except mysql.connector.Error as err:
        raise err


@app.route("/handle_update_password", methods=["PATCH"])
def handle_update_password():
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not current_password or not new_password:
        return jsonify({"error": MISSING_OLD_NEW_PASSWORD}), 400

    if not is_valid_password(current_password):
        return (
            jsonify(
                {
                    "error": MALFORMED_PASSWORD,
                    "message": {
                        "password": {"valid": False, "error": REQUIREMENT_PASSWORD}
                    },
                }
            ),
            422,
        )

    try:
        # avoid SQL injection syntax
        g.cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = g.cursor.fetchone()

        if not user or not verify_password(current_password, user.get("password")):
            return jsonify({"error": INCORRECT_PASSWORD}), 403

        hashed_password = hash_password(new_password)

        # avoid SQL injection syntax
        g.cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id)
        )
        g.db.commit()

        return jsonify({"message": SUCCESS_PASSWORD_CHANGED}), 200
    except mysql.connector.Error as err:
        raise err


@app.route("/handle_update_username", methods=["PATCH"])
def handle_update_username():
    data = request.get_json()
    new_username = data.get("username")

    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not new_username:
        return jsonify({"error": MISSING_NEW_USERNAME}), 400

    if not is_valid_username(new_username):
        return (
            jsonify(
                {
                    "error": MALFORMED_USERNAME,
                    "message": {"username": False, "error": REQUIREMENT_USERNAME},
                }
            ),
            422,
        )

    try:
        # Update username
        # avoid SQL injection syntax
        g.cursor.execute(
            "UPDATE users SET username = %s WHERE id = %s", (new_username, user_id)
        )
        g.db.commit()

        return (
            jsonify(
                {
                    "message": SUCCESS_USERNAME_CHANGED,
                    "data": {"username": new_username},
                }
            ),
            200,
        )
    except mysql.connector.Error as err:
        raise err


@app.route("/handle_delete_account", methods=["DELETE"])
def handle_delete_account():
    data = request.get_json()
    password = data.get("password")

    token = g.token
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    if not password:
        return jsonify({"error": MISSING_PASSWORD}), 400

    try:
        # Get current stored hashed password
        # avoid SQL injection syntax
        g.cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = g.cursor.fetchone()

        # Wrong given current password
        if not user or not verify_password(password, user.get("password")):
            return jsonify({"error": INCORRECT_PASSWORD}), 403

        # Delete account
        g.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        g.db.commit()

        # Development only
        del TOKENS[token]
        return jsonify({"message": SUCCESS_DATA_DELETED}), 200

    except mysql.connector.Error as err:
        raise err


@app.route('/register_fcm_token', methods=['POST'])
def register_fcm_token():
    data = request.get_json()
    fcm_token = data.get('fcm_token')
    decoded_token = g.decoded_token
    user_id = decoded_token.get('user_id')

    if not fcm_token:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # avoid SQL injection syntax
        g.cursor.execute("INSERT INTO user_fcm_tokens (user_id, fcm_token) VALUES (%s, %s) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;", (user_id, fcm_token))
        g.db.commit()
        return jsonify({'message': SUCCESS_DATA_CREATED}), 200
    except mysql.connector.Error as err:
        raise err


@app.route('/handle_periodical_submitted_location', methods=['POST'])
def handle_periodical_submitted_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    fcm_token = data.get('fcm_token')
    decoded_token = g.decoded_token
    user_id = decoded_token.get('user_id')

    if not fcm_token:
        return jsonify({"error": MISSING_DATA}), 400

    # avoid SQL injection syntax
    g.cursor.execute("select * from user_fcm_tokens where user_id = %s and fcm_token = %s", (user_id, fcm_token))
    record = g.cursor.fetchone()
    if not record:
        return jsonify({"error": INVALID_TOKEN}), 401
    
    if not latitude or not longitude:
        current_suburb_id = None
    else:
        current_suburb_id = get_suburb_id_from_geolocation(latitude, longitude)

    # avoid SQL injection syntax
    g.cursor.execute("select start_time, end_time from user_alert_time where user_id = %s and is_active = true;", (user_id,))
    alert_times = g.cursor.fetchall()

    current_time = datetime.datetime.now().time()
    current_time_as_timedelta = datetime.timedelta(hours=current_time.hour, minutes=current_time.minute, seconds=current_time.second)

    in_alert_time = False
    for alert_time in alert_times:
        start_time = alert_time.get('start_time')
        end_time = alert_time.get('end_time')
        if start_time <= current_time_as_timedelta <= end_time:
            in_alert_time = True
            break
    
    if not in_alert_time:
        return jsonify({"message": NOT_IN_ALERT_TIME}), 204
    
    # avoid SQL injection syntax
    g.cursor.execute("select uas.suburb_id, suburbs.suburb_name, weathers.weather \
                    from posts, user_alert_suburb uas, user_alert_weather uaw, weathers, suburbs \
                    where (uas.suburb_id = posts.suburb_id or uas.suburb_id = %s) and \
                    suburbs.id = uas.suburb_id and \
                    uaw.user_id = uas.user_id and \
                    uas.user_id = %s and \
                    uaw.weather_id = posts.weather_id and \
                    uaw.weather_id = weathers.id and \
                    posts.created_at >= NOW() - INTERVAL %s MINUTE;", (current_suburb_id, user_id, POST_ALERT_EXPIRY_WINDOW))
    post_result = g.cursor.fetchall()

    # handle post result
    post_result_count = {}
    for row in post_result:
        if current_suburb_id is not None and row['suburb_id'] == current_suburb_id:
            key = ('From Post', 'Current Location', row['weather'])
        else:
            key = ('From Post', row['suburb_name'], row['weather'])
        post_result_count[key] = post_result_count.get(key, 0) + 1
    eligible_result = [i for i in post_result_count.items() if i[1] > NOTIFICATION_ALERT_THRESHOLD]

    # handle api result
    g.cursor.execute("select weather, weather_id from user_alert_weather uaw, weathers \
                   where uaw.weather_id = weathers.id and \
                   uaw.user_id = %s;", (user_id,))
    user_alert_weathers = g.cursor.fetchall()
    user_alert_weather_dict = {i['weather_id']:i['weather'] for i in user_alert_weathers}
    api_current_weather_id = get_current_weather(latitude, longitude)
    
    # current location record
    for weather in user_alert_weathers:
        if api_current_weather_id == weather.get('weather_id') and datetime.datetime.now() - g.last_api_alert_time < datetime.timedelta(minutes=30):
            eligible_result.append(('From Authority', 'Current Location', weather['weather']))
            g.last_api_alert_time = datetime.datetime.now()
    
    # alert suburb record
    g.cursor.execute("select latitude, longitude, suburbs.id as suburb_id, suburb_name from suburbs, user_alert_suburb uas where uas.suburb_id = suburbs.id and uas.user_id = %s", (user_id,))
    user_alert_suburbs = g.cursor.fetchall()
    user_alert_suburb_dict = {i['suburb_id']: {'suburb_name': i['suburb_name']} for i in user_alert_suburbs}
    for suburb in user_alert_suburbs:
        api_suburb_weather_id = get_current_weather(suburb.get('latitude'), suburb.get('longitude'))
        if api_suburb_weather_id in user_alert_weather_dict:
            if suburb.get('suburb_id') != current_suburb_id:
                record = ('From Authority', user_alert_suburb_dict[suburb.get('suburb_id')]['suburb_name'], user_alert_weather_dict[api_current_weather_id])
            eligible_result.append(record)

    # if have result, send
    if len(eligible_result) >= 0:
        response_data = []
        for source, suburb_name, weather in eligible_result:
            message_title = source + ": " + weather
            message_body = suburb_name + " is " + weather
            response_data.append({'message_title': message_title, 'message_body': message_body})
            send_notifications(fcm_token, message_title, message_body)
        return jsonify({
            'message': NOTIFICATION_SENT,
            'data': response_data
        }), 201
    else:
        return jsonify({"message": NOT_MEET_THRESHOLD}), 204

def send_notifications(fcm_token: str, message_title: str, message_body: str):
    print("Sending scheduled notification...")
    message = messaging.Message(
        notification=messaging.Notification(
            title=message_title,
            body=message_body,
        ),
        data={
            'message_title': message_title,
            'message_body': message_body
        },
        token=fcm_token
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)

@app.route("/suburbs", methods=["GET"])
def get_suburbs():
    try:
        # Retrieve all suburbs
        # avoid SQL injection syntax
        g.cursor.execute("""
            SELECT id, suburb_name, postcode, latitude, longitude, state_code
            FROM suburbs
        """)
        
        suburbs = g.cursor.fetchall()

        # Format the result
        result = []
        for suburb in suburbs:
            result.append({
                'id': suburb['id'],
                'suburb_name': suburb['suburb_name'],
                'postcode': suburb['postcode'],
                'latitude': float(suburb['latitude']),
                'longitude': float(suburb['longitude']),
                'state_code': suburb['state_code']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/weathers", methods=["GET"])
def get_weathers():
    try:
        # Retrieve all weather information with category names
        
        g.cursor.execute("""
            SELECT w.id, wc.category, w.weather, w.weather_code
            FROM weathers w
            JOIN weather_cats wc ON w.category_id = wc.id
        """)
        
        weathers = g.cursor.fetchall()

        # Format the result
        result = []
        for weather in weathers:
            result.append({
                'id': weather['id'],
                'category': weather['category'],
                'weather': weather['weather'],
                'weather_code': weather['weather_code']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_saved_suburb", methods=["GET"])
def get_user_saved_suburbs():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Retrieve user saved suburbs
        # avoid SQL injection syntax
        g.cursor.execute("""
            SELECT uss.id, uss.suburb_id, uss.label, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_saved_suburb uss
            JOIN suburbs s ON uss.suburb_id = s.id
            WHERE uss.user_id = %s
        """, (user_id,))
        
        saved_suburbs = g.cursor.fetchall()

        # Format the result
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

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_saved_suburb", methods=["POST"])
def add_user_saved_suburb():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    label = data.get("label")
    suburb_id = data.get("suburb_id")

    # Check if required fields are present
    if not label or not suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the suburb exists
        # avoid SQL injection syntax
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the label or suburb_id is already used by the user
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

        # Insert new saved suburb
        g.cursor.execute(
            "INSERT INTO user_saved_suburb (user_id, suburb_id, label) VALUES (%s, %s, %s)",
            (user_id, suburb_id, label),
        )
        new_id = g.cursor.lastrowid
        g.db.commit()

        # Retrieve the inserted data
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

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/user_saved_suburb", methods=["PUT"])
def update_user_saved_suburb():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    entry_id = data.get("id")
    new_suburb_id = data.get("suburb_id")
    new_label = data.get("label")

    # Check if required fields are present
    if not entry_id or not new_suburb_id or not new_label:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the entry exists and belongs to the user
        
        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE id = %s AND user_id = %s",
            (entry_id, user_id)
        )
        existing_entry = g.cursor.fetchone()
        if not existing_entry:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the new suburb exists
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (new_suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the new label or suburb_id is already used by the user (excluding the current entry)
        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE user_id = %s AND (label = %s OR suburb_id = %s) AND id != %s",
            (user_id, new_label, new_suburb_id, entry_id)
        )
        duplicate = g.cursor.fetchone()
        if duplicate:
            if duplicate['label'] == new_label:
                return jsonify({"error": CONFLICT_SAVED_SUBURB}), 409
            else:
                return jsonify({"error": "User has already saved this suburb"}), 409

        # Update the saved suburb
        g.cursor.execute(
            "UPDATE user_saved_suburb SET suburb_id = %s, label = %s WHERE id = %s AND user_id = %s",
            (new_suburb_id, new_label, entry_id, user_id)
        )
        g.db.commit()

        # Retrieve the updated data
        g.cursor.execute("""
            SELECT uss.id, uss.suburb_id, uss.label, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_saved_suburb uss
            JOIN suburbs s ON uss.suburb_id = s.id
            WHERE uss.id = %s AND uss.user_id = %s
        """, (entry_id, user_id))
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

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/user_saved_suburb", methods=["DELETE"])
def delete_user_saved_suburb():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    entry_id = data.get("id")

    # Check if required field is present
    if not entry_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the entry exists and belongs to the user
        
        g.cursor.execute(
            "SELECT * FROM user_saved_suburb WHERE id = %s AND user_id = %s",
            (entry_id, user_id)
        )
        existing_entry = g.cursor.fetchone()
        if not existing_entry:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Delete the saved suburb
        g.cursor.execute(
            "DELETE FROM user_saved_suburb WHERE id = %s AND user_id = %s",
            (entry_id, user_id)
        )
        g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_DELETED,
            'data': {
                'id': entry_id
            }
        }), 200

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_alert_suburb", methods=["GET"])
def get_user_alert_suburbs():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Retrieve user alert suburbs
        
        g.cursor.execute("""
            SELECT uas.id, uas.suburb_id, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_alert_suburb uas
            JOIN suburbs s ON uas.suburb_id = s.id
            WHERE uas.user_id = %s
        """, (user_id,))
        
        alert_suburbs = g.cursor.fetchall()

        # Format the result
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

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_alert_suburb", methods=["POST"])
def add_user_alert_suburb():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    suburb_id = data.get("suburb_id")

    # Check if required field is present
    if not suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the suburb exists
        
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the suburb_id is already used by the user
        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE user_id = %s AND suburb_id = %s",
            (user_id, suburb_id),
        )
        existing = g.cursor.fetchone()
        if existing:
            return jsonify({"error": CONFLICT_ALERT_SUBURB}), 409

        # Insert new alert suburb
        g.cursor.execute(
            "INSERT INTO user_alert_suburb (user_id, suburb_id) VALUES (%s, %s)",
            (user_id, suburb_id),
        )
        new_id = g.cursor.lastrowid
        g.db.commit()

        # Retrieve the inserted data
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

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/user_alert_suburb", methods=["PUT"])
def update_user_alert_suburb():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    entry_id = data.get("id")
    new_suburb_id = data.get("suburb_id")

    # Check if required fields are present
    if not entry_id or not new_suburb_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the entry exists and belongs to the user
        
        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE id = %s AND user_id = %s",
            (entry_id, user_id)
        )
        existing_entry = g.cursor.fetchone()
        if not existing_entry:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the new suburb exists
        g.cursor.execute("SELECT * FROM suburbs WHERE id = %s", (new_suburb_id,))
        suburb = g.cursor.fetchone()
        if not suburb:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the new suburb_id is already used by the user (excluding the current entry)
        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE user_id = %s AND suburb_id = %s AND id != %s",
            (user_id, new_suburb_id, entry_id)
        )
        duplicate = g.cursor.fetchone()
        if duplicate:
            return jsonify({"error": CONFLICT_ALERT_SUBURB}), 409

        # Update the alert suburb
        g.cursor.execute(
            "UPDATE user_alert_suburb SET suburb_id = %s WHERE id = %s AND user_id = %s",
            (new_suburb_id, entry_id, user_id)
        )
        g.db.commit()

        # Retrieve the updated data
        g.cursor.execute("""
            SELECT uas.id, uas.suburb_id, 
                   s.suburb_name, s.postcode, s.latitude, s.longitude, s.state_code
            FROM user_alert_suburb uas
            JOIN suburbs s ON uas.suburb_id = s.id
            WHERE uas.id = %s AND uas.user_id = %s
        """, (entry_id, user_id))
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

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_alert_suburb", methods=["DELETE"])
def delete_user_alert_suburb():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    entry_id = data.get("id")

    # Check if required field is present
    if not entry_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the entry exists and belongs to the user
        
        g.cursor.execute(
            "SELECT * FROM user_alert_suburb WHERE id = %s AND user_id = %s",
            (entry_id, user_id)
        )
        existing_entry = g.cursor.fetchone()
        if not existing_entry:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Delete the saved suburb
        g.cursor.execute(
            "DELETE FROM user_alert_suburb WHERE id = %s AND user_id = %s",
            (entry_id, user_id)
        )
        g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_DELETED,
            'data': {
                'id': entry_id
            }
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

def format_timedelta(td):
    # Convert timedelta to total seconds, then extract hours, minutes, and seconds
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02}'

@app.route("/user_alert_time", methods=["GET"])
def get_user_alert_times():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Retrieve user alert times
        
        g.cursor.execute("""
            SELECT id, start_time, end_time, is_active
            FROM user_alert_time
            WHERE user_id = %s
        """, (user_id,))
        
        alert_times = g.cursor.fetchall()

        # Format the result
        result = []
        for time in alert_times:
            start_time = format_timedelta(time['start_time'])
            end_time = format_timedelta(time['end_time'])
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

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_alert_time", methods=["POST"])
def add_user_alert_time():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    is_active = data.get("is_active")

    # Check if required fields are present
    if not start_time or not end_time or is_active is None:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Convert string times to datetime.time objects
        start_time_obj = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
        end_time_obj = datetime.datetime.strptime(end_time, "%H:%M:%S").time()

        # Check if start_time is earlier than end_time
        if start_time_obj >= end_time_obj:
            return jsonify({"error": MALFORMED_TIME}), 422

        # Check for exact match of start_time and end_time for the same user
        
        g.cursor.execute("""
            SELECT * FROM user_alert_time
            WHERE user_id = %s AND start_time = %s AND end_time = %s
        """, (user_id, start_time, end_time))
        
        existing = g.cursor.fetchone()
        if existing:
            return jsonify({"error": CONFLICT_ALERT_TIME}), 409

        # Insert new alert time
        g.cursor.execute("""
            INSERT INTO user_alert_time (user_id, start_time, end_time, is_active)
            VALUES (%s, %s, %s, %s)
        """, (user_id, start_time, end_time, is_active))
        
        new_id = g.cursor.lastrowid
        g.db.commit()

        # Retrieve the inserted data
        g.cursor.execute("""
            SELECT id, start_time, end_time, is_active
            FROM user_alert_time
            WHERE id = %s
        """, (new_id,))
        
        new_alert_time = g.cursor.fetchone()

        start_time = format_timedelta(new_alert_time['start_time'])
        end_time = format_timedelta(new_alert_time['end_time'])
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
        # This occurs if the time string cannot be parsed
        return jsonify({"error": NOT_EXIST_FK}), 422
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_alert_time", methods=["PUT"])
def update_user_alert_time():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    alert_time_id = data.get("id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    is_active = data.get("is_active")

    # Check if required fields are present
    if not alert_time_id or not start_time or not end_time or is_active is None:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Convert string times to datetime.time objects
        start_time_obj = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
        end_time_obj = datetime.datetime.strptime(end_time, "%H:%M:%S").time()

        # Check if start_time is earlier than end_time
        if start_time_obj >= end_time_obj:
            return jsonify({"error": MALFORMED_TIME}), 422

        # Check if the alert time exists and belongs to the user
        
        g.cursor.execute("""
            SELECT * FROM user_alert_time
            WHERE id = %s AND user_id = %s
        """, (alert_time_id, user_id))
        existing = g.cursor.fetchone()
        if not existing:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check for exact match of start_time and end_time for the same user (excluding current entry)
        g.cursor.execute("""
            SELECT * FROM user_alert_time
            WHERE user_id = %s AND start_time = %s AND end_time = %s AND id != %s
        """, (user_id, start_time, end_time, alert_time_id))
        
        duplicate = g.cursor.fetchone()
        if duplicate:
            return jsonify({"error": CONFLICT_ALERT_TIME}), 409

        # Update the alert time
        g.cursor.execute("""
            UPDATE user_alert_time
            SET start_time = %s, end_time = %s, is_active = %s
            WHERE id = %s AND user_id = %s
        """, (start_time, end_time, is_active, alert_time_id, user_id))
        
        g.db.commit()

        # Retrieve the updated data
        g.cursor.execute("""
            SELECT id, start_time, end_time, is_active
            FROM user_alert_time
            WHERE id = %s
        """, (alert_time_id,))
        
        updated_alert_time = g.cursor.fetchone()

        start_time = format_timedelta(updated_alert_time['start_time'])
        end_time = format_timedelta(updated_alert_time['end_time'])
        result = {
            'id': updated_alert_time['id'],
            'start_time': start_time,
            'end_time': end_time,
            'is_active': bool(updated_alert_time['is_active'])
        }

        return jsonify({
            'message': SUCCESS_DATA_UPDATED,
            'data': result
        }), 200

    except ValueError:
        # This occurs if the time string cannot be parsed
        return jsonify({"error": NOT_EXIST_FK}), 422
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/user_alert_time", methods=["DELETE"])
def delete_user_alert_time():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    alert_time_id = data.get("id")

    # Check if required field is present
    if not alert_time_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the alert time exists and belongs to the user
        
        g.cursor.execute("""
            SELECT * FROM user_alert_time
            WHERE id = %s AND user_id = %s
        """, (alert_time_id, user_id))
        existing = g.cursor.fetchone()
        if not existing:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Delete the alert time
        g.cursor.execute("""
            DELETE FROM user_alert_time
            WHERE id = %s AND user_id = %s
        """, (alert_time_id, user_id))
        
        g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_DELETED,
            'data': {
                'id': alert_time_id
            }
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/user_alert_weather", methods=["GET"])
def get_user_alert_weathers():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Retrieve user alert weathers with joins to get weather and category information
        
        g.cursor.execute("""
            SELECT uaw.id, uaw.weather_id, wc.category, w.weather, w.weather_code
            FROM user_alert_weather uaw
            JOIN weathers w ON uaw.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE uaw.user_id = %s
        """, (user_id,))
        
        alert_weathers = g.cursor.fetchall()

        # Format the result
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

    except mysql.connector.Error as err:
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
    except mysql.connector.Error as err:
        print(f"Database error in batch delete: {err}")
        return False

@app.route("/user_alert_weather", methods=["POST"])
def add_user_alert_weather():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    weather_id = data.get("weather_id")

    if not weather_id or weather_id not in WEATHER_ONE_TO_N:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if any of the weather_ids already exist for the user
        weather_ids = WEATHER_ONE_TO_N[weather_id]
        placeholders = ', '.join(['%s'] * len(weather_ids))
        g.cursor.execute(f"""
            SELECT weather_id FROM user_alert_weather
            WHERE user_id = %s AND weather_id IN ({placeholders})
        """, (user_id, *weather_ids))
        existing = g.cursor.fetchall()
        if existing:
            return jsonify({"error": "User has already saved this weather alert"}), 409

        # Batch insert
        for w_id in weather_ids:
            g.cursor.execute(
                "INSERT INTO user_alert_weather (user_id, weather_id) VALUES (%s, %s)",
                (user_id, w_id)
            )
        g.db.commit()

        # Retrieve the inserted data for the requested weather_id
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

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        raise err

@app.route("/user_alert_weather", methods=["PUT"])
def update_user_alert_weather():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    alert_id = data.get("id")
    new_weather_id = data.get("weather_id")

    if not alert_id or new_weather_id is None or new_weather_id not in WEATHER_ONE_TO_N:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the alert exists and belongs to the user
        g.cursor.execute("""
            SELECT weather_id FROM user_alert_weather
            WHERE id = %s AND user_id = %s
        """, (alert_id, user_id))
        existing_alert = g.cursor.fetchone()
        if not existing_alert:
            return jsonify({"error": NOT_EXIST_FK}), 422

        old_weather_id = existing_alert['weather_id']

        # Batch delete old weather alerts
        batch_delete_user_alert_weather(user_id, old_weather_id)

        # Batch insert new weather alerts
        weather_ids = WEATHER_ONE_TO_N[new_weather_id]
        for w_id in weather_ids:
            g.cursor.execute(
                "INSERT INTO user_alert_weather (user_id, weather_id) VALUES (%s, %s)",
                (user_id, w_id)
            )
        g.db.commit()

        # Retrieve the updated data for the requested weather_id
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

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        raise err

@app.route("/user_alert_weather", methods=["DELETE"])
def delete_user_alert_weather():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    alert_id = data.get("id")

    if not alert_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the alert exists and belongs to the user
        g.cursor.execute("""
            SELECT weather_id FROM user_alert_weather
            WHERE id = %s AND user_id = %s
        """, (alert_id, user_id))
        existing_alert = g.cursor.fetchone()
        if not existing_alert:
            return jsonify({"error": NOT_EXIST_FK}), 422

        weather_id = existing_alert['weather_id']

        # Batch delete
        if batch_delete_user_alert_weather(user_id, weather_id):
            return jsonify({
                'message': SUCCESS_DATA_DELETED,
                'data': {
                    'id': alert_id
                }
            }), 200
        else:
            return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500


def retrieve_suburb(latitude, longitude):
    if latitude is None or longitude is None:
        return jsonify({"error": "Missing or invalid latitude/longitude"}), 400

    try:
        # Make request to Geoapify API
        url = f"https://api.geoapify.com/v1/geocode/reverse?lat={latitude}&lon={longitude}&format=json&apiKey={GEOAPIFY_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        data = response.json()

        if not data.get('results'):
            return jsonify({"error": "No suburb found for the given coordinates"}), 404

        location = data['results'][0]
        country = location.get('country')
        state_code = location.get('state_code')
        city = location.get('city')
        postcode = location.get('postcode')

        if not city or not postcode:
            return jsonify({"error": "Incomplete location data returned from API"}), 404
        
        if country != 'Australia' or state_code != 'QLD':
            return None
        
        g.cursor.execute("SELECT * FROM suburbs WHERE postcode = %s", (postcode,))
        suburbs = g.cursor.fetchall()

        correct_suburb = None
        if len(suburbs) > 1:
            for suburb in suburbs:
                if suburb['suburb_name'] == city:
                    correct_suburb = suburb
                    break
        if correct_suburb is None:
            correct_suburb = suburbs[0]

        result = {
            'suburb_id': correct_suburb['id'],
            'suburb_name': correct_suburb['suburb_name'],
            'postcode': correct_suburb['postcode'],
            'state_code': correct_suburb['state_code'],
            'formatted': location.get('formatted', ''),
            'address_line1': location.get('address_line1', '')
        }

        return result, None  # Return the result and no error

    except requests.RequestException as e:
        print(f"Geoapify API error: {str(e)}")
        return None, "Error connecting to external API"
    except mysql.connector.Error as err:
        raise err
    except Exception as e:
        raise e

@app.route("/posts", methods=["POST"])
def create_post():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    weather_id = data.get("weather_id")
    comment = data.get("comment", "")  # Optional, default to empty string

    # Check if required fields are present
    if not latitude or not longitude or not weather_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the weather_id exists
        
        g.cursor.execute("SELECT * FROM weathers WHERE id = %s", (weather_id,))
        weather = g.cursor.fetchone()
        if not weather:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Retrieve suburb information
        suburb_data, error = retrieve_suburb(latitude, longitude)
        if error:
            if error == "No suburb found for the given coordinates":
                return jsonify({"error": error}), 404
            else:
                raise KeyError

        # Insert new post
        g.cursor.execute("""
            INSERT INTO posts (user_id, latitude, longitude, suburb_id, weather_id, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, latitude, longitude, suburb_data['suburb_id'], weather_id, comment))
        
        new_post_id = g.cursor.lastrowid
        g.db.commit()

        # Retrieve the inserted data with all required details
        g.cursor.execute("""
            SELECT p.*, s.suburb_name, s.postcode, s.state_code, w.weather, w.weather_code
            FROM posts p
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            WHERE p.id = %s
        """, (new_post_id,))
        
        new_post = g.cursor.fetchone()

        result = {
            'id': new_post['id'],
            'latitude': float(new_post['latitude']),
            'longitude': float(new_post['longitude']),
            'suburb_id': new_post['suburb_id'],
            'suburb_name': new_post['suburb_name'],
            'postcode': new_post['postcode'],
            'state_code': new_post['state_code'],
            'weather_id': new_post['weather_id'],
            'weather': new_post['weather'],
            'weather_code': new_post['weather_code'],
            'created_at': new_post['created_at'].isoformat(),
            'likes': new_post['likes'],
            'views': new_post['views'],
            'reports': new_post['reports'],
            'is_active': bool(new_post['is_active']),
            'comment': new_post['comment']
        }

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': result
        }), 201

    except mysql.connector.Error as err:
        raise err

@app.route("/posts", methods=["DELETE"])
def delete_post():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    post_id = data.get("id")

    # Check if required field is present
    if not post_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the post exists and belongs to the user
        
        g.cursor.execute("""
            SELECT * FROM posts
            WHERE id = %s AND user_id = %s
        """, (post_id, user_id))
        existing_post = g.cursor.fetchone()
        if not existing_post:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Delete the post
        g.cursor.execute("""
            DELETE FROM posts
            WHERE id = %s AND user_id = %s
        """, (post_id, user_id))
        
        g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_DELETED,
            'data': {
                'id': post_id
            }
        }), 200

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/posts", methods=["GET"])
def get_user_posts():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Retrieve all posts for the user with required details
        
        g.cursor.execute("""
            SELECT p.id as post_id, p.latitude, p.longitude, p.suburb_id, s.suburb_name,
                   p.weather_id, wc.category as weather_category, w.weather, w.weather_code,
                   p.created_at, p.likes, p.views, p.reports, p.is_active, p.comment
            FROM posts p
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
        """, (user_id,))
        
        user_posts = g.cursor.fetchall()

        # Format the result
        result = []
        for post in user_posts:
            result.append({
                'post_id': post['post_id'],
                'latitude': float(post['latitude']),
                'longitude': float(post['longitude']),
                'suburb_id': post['suburb_id'],
                'suburb_name': post['suburb_name'],
                'weather_id': post['weather_id'],
                'weather_category': post['weather_category'],
                'weather': post['weather'],
                'weather_code': post['weather_code'],
                'created_at': post['created_at'].isoformat(),
                'likes': post['likes'],
                'views': post['views'],
                'reports': post['reports'],
                'is_active': bool(post['is_active']),
                'comment': post['comment']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except mysql.connector.Error as err:
        # Log the error for debugging (you might want to implement proper logging)
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/posts/view", methods=["GET"])
def get_viewed_posts():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Retrieve all viewed posts for the user with required details
        
        g.cursor.execute("""
            SELECT p.id as post_id, p.latitude, p.longitude, p.suburb_id, s.suburb_name,
                   p.weather_id, wc.category as weather_category, w.weather, w.weather_code,
                   p.created_at, p.likes, p.views, p.reports, p.is_active, p.comment
            FROM user_view_post uvp
            JOIN posts p ON uvp.post_id = p.id
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE uvp.user_id = %s
            ORDER BY p.created_at DESC
        """, (user_id,))
        
        viewed_posts = g.cursor.fetchall()

        # Format the result
        result = []
        for post in viewed_posts:
            result.append({
                'post_id': post['post_id'],
                'latitude': float(post['latitude']),
                'longitude': float(post['longitude']),
                'suburb_id': post['suburb_id'],
                'suburb_name': post['suburb_name'],
                'weather_id': post['weather_id'],
                'weather_category': post['weather_category'],
                'weather': post['weather'],
                'weather_code': post['weather_code'],
                'created_at': post['created_at'].isoformat(),
                'likes': post['likes'],
                'views': post['views'],
                'reports': post['reports'],
                'is_active': bool(post['is_active']),
                'comment': post['comment']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/posts/view", methods=["POST"])
def add_viewed_post():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    post_id = data.get("post_id")

    # Check if required field is present
    if not post_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the post exists
        
        g.cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = g.cursor.fetchone()
        if not post:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the view record already exists
        g.cursor.execute(
            "SELECT * FROM user_view_post WHERE user_id = %s AND post_id = %s",
            (user_id, post_id)
        )
        existing_view = g.cursor.fetchone()

        if not existing_view:
            # Insert new view record
            g.cursor.execute(
                "INSERT INTO user_view_post (user_id, post_id) VALUES (%s, %s)",
                (user_id, post_id)
            )
            
            # Increment the views count in the posts table
            g.cursor.execute(
                "UPDATE posts SET views = views + 1 WHERE id = %s",
                (post_id,)
            )
            
            g.db.commit()

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': {
                'post_id': post_id
            }
        }), 201

    except mysql.connector.Error as err:
        raise err

@app.route("/posts/like", methods=["GET"])
def get_liked_posts():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        
        g.cursor.execute("""
            SELECT p.id as post_id, p.latitude, p.longitude, p.suburb_id, s.suburb_name,
                   p.weather_id, wc.category as weather_category, w.weather, w.weather_code,
                   p.created_at, p.likes, p.views, p.reports, p.is_active, p.comment
            FROM user_like_post ulp
            JOIN posts p ON ulp.post_id = p.id
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE ulp.user_id = %s
            ORDER BY p.created_at DESC
        """, (user_id,))
        
        liked_posts = g.cursor.fetchall()

        result = []
        for post in liked_posts:
            result.append({
                'post_id': post['post_id'],
                'latitude': float(post['latitude']),
                'longitude': float(post['longitude']),
                'suburb_id': post['suburb_id'],
                'suburb_name': post['suburb_name'],
                'weather_id': post['weather_id'],
                'weather_category': post['weather_category'],
                'weather': post['weather'],
                'weather_code': post['weather_code'],
                'created_at': post['created_at'].isoformat(),
                'likes': post['likes'],
                'views': post['views'],
                'reports': post['reports'],
                'is_active': bool(post['is_active']),
                'comment': post['comment']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/posts/report", methods=["GET"])
def get_reported_posts():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        
        g.cursor.execute("""
            SELECT p.id as post_id, urp.report_comment, urp.created_at as report_created_at,
                   p.latitude, p.longitude, p.suburb_id, s.suburb_name,
                   p.weather_id, wc.category as weather_category, w.weather, w.weather_code,
                   p.created_at, p.likes, p.views, p.reports, p.is_active, p.comment
            FROM user_report_post urp
            JOIN posts p ON urp.post_id = p.id
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE urp.user_id = %s
            ORDER BY urp.created_at DESC
        """, (user_id,))
        
        reported_posts = g.cursor.fetchall()

        result = []
        for post in reported_posts:
            result.append({
                'post_id': post['post_id'],
                'report_comment': post['report_comment'],
                'created_at': post['report_created_at'].isoformat(),
                'latitude': float(post['latitude']),
                'longitude': float(post['longitude']),
                'suburb_id': post['suburb_id'],
                'suburb_name': post['suburb_name'],
                'weather_id': post['weather_id'],
                'weather_category': post['weather_category'],
                'weather': post['weather'],
                'weather_code': post['weather_code'],
                'post_created_at': post['created_at'].isoformat(),
                'likes': post['likes'],
                'views': post['views'],
                'reports': post['reports'],
                'is_active': bool(post['is_active']),
                'comment': post['comment']
            })

        return jsonify({
            'message': SUCCESS_DATA_RETRIEVED,
            'data': result
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@app.route("/get_posts", methods=["GET"])
def get_filtered_posts():
    # Extract query parameters
    post_id = request.args.get('id')
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    suburb_id = request.args.get('suburb_id')
    weather_id = request.args.get('weather_id')
    likes = request.args.get('likes')
    views = request.args.get('views')
    reports_le = request.args.get('reports_le')
    reports_lg = request.args.get('reports_le')
    is_active = request.args.get('is_active')
    time_interval = request.args.get('time_interval')
    limit = request.args.get('limit', 50)

    # Check if latitude and longitude are both provided or both missing
    if (latitude is None) != (longitude is None):
        return jsonify({"error": "Latitude and longitude must be both provided or both missing"}), 400
    
    # Check if reports_le is bigger than reports_lg
    if reports_le is not None and reports_lg is not None:
        if reports_le < reports_lg:
            return jsonify({"error": "Reposts amount range error"}), 400

    try:
        # Start building the SQL query
        query = """
            SELECT p.id as post_id, p.latitude, p.longitude, p.suburb_id, s.suburb_name,
                   p.weather_id, wc.category as weather_category, w.weather, w.weather_code,
                   p.created_at, p.likes, p.views, p.reports, p.is_active, p.comment
            FROM posts p
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            WHERE 1=1
        """
        params = []

        # Add filters to the query
        if post_id:
            query += " AND p.id = %s"
            params.append(int(post_id))
        if latitude and longitude:
            query += " AND p.latitude = %s AND p.longitude = %s"
            params.extend([float(latitude), float(longitude)])
        if suburb_id:
            query += " AND p.suburb_id = %s"
            params.append(int(suburb_id))
        if weather_id:
            query += " AND p.weather_id = %s"
            params.append(int(weather_id))
        if likes:
            query += " AND p.likes >= %s"
            params.append(int(likes))
        if views:
            query += " AND p.views >= %s"
            params.append(int(views))
        if reports_le:
            query += " AND p.reports <= %s"
            params.append(int(reports_le))
        if reports_lg:
            query += " AND p.reports >= %s"
            params.append(int(reports_le))
        if is_active is not None:
            query += " AND p.is_active = %s"
            params.append(is_active.lower() == 'true')
        if time_interval:
            time_threshold = datetime.datetime.now(brisbane_tz) - datetime.timedelta(minutes=int(time_interval))
            query += " AND p.created_at >= %s"
            params.append(time_threshold)

        # Add order by and limit
        query += " ORDER BY p.created_at DESC LIMIT %s"
        params.append(int(limit))

        # Execute the query
        
        g.cursor.execute(query, tuple(params))
        posts = g.cursor.fetchall()

        return jsonify({
            'message': 'Data retrieved Successfully',
            'data': posts
        }), 200

    except ValueError as ve:
        return jsonify({"error": "Invalid parameter format"}), 422
    except mysql.connector.Error as err:
        raise err
    except Exception as e:
        raise e

@app.route("/posts/like/<int:post_id>", methods=["GET"])
def check_user_liked_post(post_id):
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
        # Check if the post exists
        
        g.cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = g.cursor.fetchone()
        if not post:
            return jsonify({"error": NOT_FOUND_RECORDS}), 404

        # Check if the user has liked the post
        g.cursor.execute("""
            SELECT * FROM user_like_post
            WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id))
        
        like_record = g.cursor.fetchone()
        
        return jsonify({
            'post_id': post_id,
            'liked': bool(like_record)
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/posts/like", methods=["POST"])
def toggle_post_like():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    post_id = data.get("post_id")

    # Check if required field is present
    if not post_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the post exists
        
        g.cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = g.cursor.fetchone()
        if not post:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Check if the user has already liked the post
        g.cursor.execute("""
            SELECT * FROM user_like_post
            WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id))
        
        like_record = g.cursor.fetchone()
        
        if like_record:
            # User has already liked the post, so unlike it
            g.cursor.execute("""
                DELETE FROM user_like_post
                WHERE user_id = %s AND post_id = %s
            """, (user_id, post_id))
            liked = False
        else:
            # User hasn't liked the post, so like it
            g.cursor.execute("""
                INSERT INTO user_like_post (user_id, post_id)
                VALUES (%s, %s)
            """, (user_id, post_id))
            liked = True

        # Update the likes count in the posts table
        g.cursor.execute("""
            UPDATE posts
            SET likes = likes + %s
            WHERE id = %s
        """, (1 if liked else -1, post_id))

        g.db.commit()

        return jsonify({
            'post_id': post_id,
            'liked': liked
        }), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
    
@app.route("/posts/report", methods=["POST"])
def report_post():
    # Get user_id from the token (already verified in @app.before_request)
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    # Get data from request
    data = request.get_json()
    post_id = data.get("post_id")
    report_comment = data.get("report_comment")

    # Check if required fields are present
    if not post_id or not report_comment:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if the post exists
        
        g.cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = g.cursor.fetchone()
        if not post:
            return jsonify({"error": NOT_EXIST_FK}), 422

        # Insert the report
        g.cursor.execute("""
            INSERT INTO user_report_post (user_id, post_id, report_comment)
            VALUES (%s, %s, %s)
        """, (user_id, post_id, report_comment))

        # Update the reports count in the posts table
        g.cursor.execute("""
            UPDATE posts
            SET reports = reports + 1
            WHERE id = %s
        """, (post_id,))

        g.db.commit()

        # Fetch the updated post details
        g.cursor.execute("""
            SELECT p.*, s.suburb_name, wc.category as weather_category, w.weather, w.weather_code,
                   urp.report_comment, urp.created_at as report_created_at
            FROM posts p
            JOIN suburbs s ON p.suburb_id = s.id
            JOIN weathers w ON p.weather_id = w.id
            JOIN weather_cats wc ON w.category_id = wc.id
            JOIN user_report_post urp ON p.id = urp.post_id
            WHERE p.id = %s AND urp.user_id = %s
        """, (post_id, user_id))
        
        reported_post = g.cursor.fetchone()

        result = {
            'post_id': reported_post['id'],
            'report_comment': reported_post['report_comment'],
            'created_at': reported_post['report_created_at'].isoformat(),
            'latitude': float(reported_post['latitude']),
            'longitude': float(reported_post['longitude']),
            'suburb_id': reported_post['suburb_id'],
            'suburb_name': reported_post['suburb_name'],
            'weather_id': reported_post['weather_id'],
            'weather_category': reported_post['weather_category'],
            'weather': reported_post['weather'],
            'weather_code': reported_post['weather_code'],
            'post_created_at': reported_post['created_at'].isoformat(),
            'likes': reported_post['likes'],
            'views': reported_post['views'],
            'reports': reported_post['reports'],
            'is_active': bool(reported_post['is_active']),
            'comment': reported_post['comment']
        }

        return jsonify({
            'message': SUCCESS_DATA_CREATED,
            'data': result
        }), 201

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500


if __name__ == "__main__":
    load_token_store()
    app.run()
