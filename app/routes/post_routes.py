from flask import Blueprint, request, jsonify, g
import psycopg2
import datetime
import requests
import pytz
from firebase_admin import messaging
from ..utils.auth import token_required, optional_token
from ..utils.constants import *

post_bp = Blueprint('post', __name__)

brisbane_tz = pytz.timezone('Australia/Brisbane')

def retrieve_suburb(latitude, longitude):
    from flask import current_app
    
    if latitude is None or longitude is None:
        return None, "Missing or invalid latitude/longitude"

    try:
        url = f"https://api.geoapify.com/v1/geocode/reverse?lat={latitude}&lon={longitude}&format=json&apiKey={current_app.config['GEOAPIFY_API_KEY']}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        if not data.get('results'):
            return None, "No suburb found for the given coordinates"

        location = data['results'][0]
        country = location.get('country')
        state_code = location.get('state_code')
        city = location.get('city')
        postcode = location.get('postcode')

        if not city or not postcode:
            return None, "Incomplete location data returned from API"
        
        if country != 'Australia' or state_code != 'QLD':
            return None, "Location not in Queensland, Australia"
        
        g.cursor.execute("SELECT * FROM suburbs WHERE postcode = %s", (postcode,))
        suburbs = g.cursor.fetchall()

        correct_suburb = None
        if len(suburbs) > 1:
            for suburb in suburbs:
                if suburb['suburb_name'] == city:
                    correct_suburb = suburb
                    break
        if correct_suburb is None:
            correct_suburb = suburbs[0] if suburbs else None

        if not correct_suburb:
            return None, "Suburb not found in database"

        result = {
            'suburb_id': correct_suburb['id'],
            'suburb_name': correct_suburb['suburb_name'],
            'postcode': correct_suburb['postcode'],
            'state_code': correct_suburb['state_code'],
            'formatted': location.get('formatted', ''),
            'address_line1': location.get('address_line1', '')
        }

        return result, None

    except requests.RequestException as e:
        print(f"Geoapify API error: {str(e)}")
        return None, "Error connecting to external API"
    except psycopg2.Error as err:
        g.db.rollback()
        raise err
    except Exception as e:
        raise e

@post_bp.route("/posts", methods=["POST"])
@token_required
def create_post():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    weather_id = data.get("weather_id")
    comment = data.get("comment", "")

    if not latitude or not longitude or not weather_id:
        return jsonify({"error": MISSING_DATA}), 400

    try:
        g.cursor.execute("SELECT * FROM weathers WHERE id = %s", (weather_id,))
        weather = g.cursor.fetchone()
        if not weather:
            return jsonify({"error": NOT_EXIST_FK}), 422

        suburb_data, error = retrieve_suburb(latitude, longitude)
        if error:
            if error == "No suburb found for the given coordinates":
                return jsonify({"error": error}), 404
            else:
                return jsonify({"error": error}), 400

        g.cursor.execute("""
            INSERT INTO posts (user_id, latitude, longitude, suburb_id, weather_id, comment)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (user_id, latitude, longitude, suburb_data['suburb_id'], weather_id, comment))
        
        new_post_id = g.cursor.fetchone()['id']
        g.db.commit()

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

    except psycopg2.Error as err:
        g.db.rollback()
        raise err

@post_bp.route("/posts", methods=["GET"])
@token_required
def get_user_posts():
    decoded_token = g.decoded_token
    user_id = decoded_token.get("user_id")

    try:
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

    except psycopg2.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500

@post_bp.route("/get_posts", methods=["GET"])
@optional_token
def get_filtered_posts():
    post_id = request.args.get('id')
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    suburb_id = request.args.get('suburb_id')
    weather_id = request.args.get('weather_id')
    likes = request.args.get('likes')
    views = request.args.get('views')
    reports_le = request.args.get('reports_le')
    reports_lg = request.args.get('reports_lg')
    is_active = request.args.get('is_active')
    time_interval = request.args.get('time_interval')
    limit = request.args.get('limit', 50)

    if (latitude is None) != (longitude is None):
        return jsonify({"error": "Latitude and longitude must be both provided or both missing"}), 400
    
    if reports_le is not None and reports_lg is not None:
        if int(reports_le) < int(reports_lg):
            return jsonify({"error": "Reports amount range error"}), 400

    try:
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
            params.append(int(reports_lg))
        if is_active is not None:
            query += " AND p.is_active = %s"
            params.append(is_active.lower() == 'true')
        if time_interval:
            time_threshold = datetime.datetime.now(brisbane_tz) - datetime.timedelta(minutes=int(time_interval))
            query += " AND p.created_at >= %s"
            params.append(time_threshold)

        query += " ORDER BY p.created_at DESC LIMIT %s"
        params.append(int(limit))

        g.cursor.execute(query, tuple(params))
        posts = g.cursor.fetchall()

        return jsonify({
            'message': 'Data retrieved Successfully',
            'data': posts
        }), 200

    except ValueError as ve:
        return jsonify({"error": "Invalid parameter format"}), 422
    except psycopg2.Error as err:
        g.db.rollback()
        raise err
    except Exception as e:
        raise e