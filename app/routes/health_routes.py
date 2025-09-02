from flask import Blueprint, jsonify
from ..models.database import get_db_connection, return_db_connection
import psycopg2

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker and monitoring"""
    try:
        # Test database connection
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return_db_connection(db)
        
        return jsonify({
            'status': 'healthy',
            'message': 'API is running and database is accessible',
            'database': 'connected'
        }), 200
        
    except psycopg2.Error as e:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Database connection failed',
            'database': 'disconnected',
            'error': str(e)
        }), 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Health check failed',
            'error': str(e)
        }), 503