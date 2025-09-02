# Gunicorn configuration file
import os
from config import Config

# Server socket
bind = f"{Config.HOST}:{Config.PORT}"

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', '4'))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 10

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'pixelweather-api'

# Preload app for better performance
preload_app = True

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190