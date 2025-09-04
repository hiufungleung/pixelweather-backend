from flask import Blueprint, request, jsonify, g
import psycopg2
import datetime
import requests
from firebase_admin import messaging
from ..utils.auth import token_required
from ..utils.constants import *

notification_bp = Blueprint('notification', __name__)

def get_suburb_id_from_geolocation(latitude: str, longitude: str) -> int | None:
    from flask import current_app
    
    url = f"https://api.geoapify.com/v1/geocode/reverse?lat={latitude}&lon={longitude}&apiKey={current_app.config['GEOAPIFY_API_KEY']}"

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
    
    g.cursor.execute("SELECT * FROM suburbs WHERE postcode = %s", (postcode,))
    suburbs = g.cursor.fetchall()

    suburb_id = None
    if len(suburbs) > 1:
        for suburb in suburbs:
            if suburb['suburb_name'] == suburb_name:
                suburb_id = suburb['suburb_id']
                break
    if suburb_id is None and suburbs:
        suburb_id = suburbs[0].get('id')
    return suburb_id

def get_current_weather(latitude: str, longitude: str) -> int | None:
    from flask import current_app
    
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&appid={current_app.config['OPEN_WEATHER_API_KEY']}"

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

    g.cursor.execute("SELECT * FROM weathers WHERE weather_code = %s", (weather_code,))
    weather_result = g.cursor.fetchone()
    weather_id = weather_result.get('id') if weather_result else None
    return weather_id

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

@notification_bp.route('/register_fcm_token', methods=['POST'])
@token_required
def register_fcm_token():
    data = request.get_json()
    fcm_token = data.get('fcm_token')
    decoded_token = g.decoded_token
    user_id = decoded_token.get('user_id')

    if not fcm_token:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        # Check if this user_id and fcm_token combination already exists
        g.cursor.execute("""
            SELECT id FROM user_fcm_tokens 
            WHERE user_id = %s AND fcm_token = %s
        """, (user_id, fcm_token))
        existing_token = g.cursor.fetchone()
        
        if existing_token:
            # Update the existing record
            g.cursor.execute("""
                UPDATE user_fcm_tokens 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = %s AND fcm_token = %s
            """, (user_id, fcm_token))
        else:
            # Insert new record
            g.cursor.execute("""
                INSERT INTO user_fcm_tokens (user_id, fcm_token, created_at, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, fcm_token))
        
        g.db.commit()
        return jsonify({'message': SUCCESS_DATA_CREATED}), 200
    except psycopg2.Error as err:
        g.db.rollback()
        raise err

@notification_bp.route('/handle_periodical_submitted_location', methods=['POST'])
@token_required
def handle_periodical_submitted_location():
    from flask import current_app
    
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    fcm_token = data.get('fcm_token')
    decoded_token = g.decoded_token
    user_id = decoded_token.get('user_id')

    if not fcm_token:
        return jsonify({"error": MISSING_DATA}), 400

    g.cursor.execute("select * from user_fcm_tokens where user_id = %s and fcm_token = %s", (user_id, fcm_token))
    record = g.cursor.fetchone()
    if not record:
        return jsonify({"error": INVALID_TOKEN}), 401
    
    if not latitude or not longitude:
        current_suburb_id = None
    else:
        current_suburb_id = get_suburb_id_from_geolocation(latitude, longitude)

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
    
    g.cursor.execute("select uas.suburb_id, suburbs.suburb_name, weathers.weather \
                    from posts, user_alert_suburb uas, user_alert_weather uaw, weathers, suburbs \
                    where (uas.suburb_id = posts.suburb_id or uas.suburb_id = %s) and \
                    suburbs.id = uas.suburb_id and \
                    uaw.user_id = uas.user_id and \
                    uas.user_id = %s and \
                    uaw.weather_id = posts.weather_id and \
                    uaw.weather_id = weathers.id and \
                    posts.created_at >= NOW() - INTERVAL '%s MINUTES';", (current_suburb_id, user_id, current_app.config['POST_ALERT_EXPIRY_WINDOW']))
    post_result = g.cursor.fetchall()

    post_result_count = {}
    for row in post_result:
        if current_suburb_id is not None and row['suburb_id'] == current_suburb_id:
            key = ('From Post', 'Current Location', row['weather'])
        else:
            key = ('From Post', row['suburb_name'], row['weather'])
        post_result_count[key] = post_result_count.get(key, 0) + 1
    eligible_result = [i for i in post_result_count.items() if i[1] > current_app.config['NOTIFICATION_ALERT_THRESHOLD']]

    g.cursor.execute("select weather, weather_id from user_alert_weather uaw, weathers \
                   WHERE uaw.weather_id = weathers.id AND \
                   uaw.user_id = %s;", (user_id,))
    user_alert_weathers = g.cursor.fetchall()
    user_alert_weather_dict = {i['weather_id']:i['weather'] for i in user_alert_weathers}
    api_current_weather_id = get_current_weather(latitude, longitude)
    
    for weather in user_alert_weathers:
        try:
            if api_current_weather_id == weather.get('weather_id') and datetime.datetime.now() - g.last_api_alert_time < datetime.timedelta(minutes=30):
                eligible_result.append((('From Authority', 'Current Location', weather['weather']), 1))
                g.last_api_alert_time = datetime.datetime.now()
        except AttributeError:
            g.last_api_alert_time = datetime.datetime.now()
    
    g.cursor.execute("select latitude, longitude, suburbs.id as suburb_id, suburb_name from suburbs, user_alert_suburb uas where uas.suburb_id = suburbs.id and uas.user_id = %s", (user_id,))
    user_alert_suburbs = g.cursor.fetchall()
    user_alert_suburb_dict = {i['suburb_id']: {'suburb_name': i['suburb_name']} for i in user_alert_suburbs}
    for suburb in user_alert_suburbs:
        api_suburb_weather_id = get_current_weather(suburb.get('latitude'), suburb.get('longitude'))
        if api_suburb_weather_id in user_alert_weather_dict:
            if suburb.get('suburb_id') != current_suburb_id:
                record = (('From Authority', user_alert_suburb_dict[suburb.get('suburb_id')]['suburb_name'], user_alert_weather_dict[api_current_weather_id]), 1)
            eligible_result.append(record)

    if len(eligible_result) > 0:
        response_data = []
        for item in eligible_result:
            if isinstance(item, tuple) and len(item) == 2:
                source, suburb_name, weather = item[0]
            else:
                source, suburb_name, weather = item
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