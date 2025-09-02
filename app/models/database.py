import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from flask import current_app, g

connection_pool = None

def init_db_pool():
    """Initialize PostgreSQL connection pool"""
    global connection_pool
    db_config = {
        'host': current_app.config['DB_HOST'],
        'port': current_app.config['DB_PORT'],
        'user': current_app.config['DB_USER'],
        'password': current_app.config['DB_PASSWORD'],
        'database': current_app.config['DB_NAME'],
        'options': f"-c search_path={current_app.config['DB_SCHEMA']}"
    }
    
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=32,
            **db_config
        )
        print("PostgreSQL connection pool created successfully")
    except Exception as e:
        print(f"Error creating PostgreSQL connection pool: {e}")
        raise e

def get_db_connection():
    """Get PostgreSQL connection from pool"""
    if connection_pool is None:
        init_db_pool()
    
    try:
        connection = connection_pool.getconn()
        return connection
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        raise e

def return_db_connection(connection):
    """Return connection to pool"""
    if connection_pool and connection:
        connection_pool.putconn(connection)

def get_db_cursor(connection):
    """Get cursor with dictionary-like row factory"""
    return connection.cursor(cursor_factory=RealDictCursor)

def close_db_connection(exception):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        return_db_connection(db)