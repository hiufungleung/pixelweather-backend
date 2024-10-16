import sys
import os

sys.path.insert(0, "/var/www/pixelweather")

os.environ["FLASK_APP"] = "pixelweather.app"

from pixelweather.app import app as application
