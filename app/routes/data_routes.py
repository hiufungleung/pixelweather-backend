from flask import Blueprint, request, jsonify, g
import psycopg2
from ..utils.auth import token_required, optional_token
from ..utils.constants import *

data_bp = Blueprint('data', __name__)

@data_bp.route("/suburbs", methods=["GET"])
@optional_token
def get_suburbs():
    try:
        g.cursor.execute("""
            SELECT id, suburb_name, postcode, latitude, longitude, state_code
            FROM suburbs
        """)
        
        suburbs = g.cursor.fetchall()

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

    except psycopg2.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
@data_bp.route("/weathers", methods=["GET"])
@optional_token
def get_weathers():
    try:
        g.cursor.execute("""
            SELECT w.id, wc.category, w.weather, w.weather_code
            FROM weathers w
            JOIN weather_cats wc ON w.category_id = wc.id
        """)
        
        weathers = g.cursor.fetchall()

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

    except psycopg2.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': INTERNAL_SERVER_ERROR}), 500
