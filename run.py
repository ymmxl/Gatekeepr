# -*- encoding: utf-8 -*-

import os
from   flask_migrate import Migrate
from   flask_minify  import Minify
from   sys import exit
import logging
from apps.config import config_dict
from apps import create_app, db

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected [Debug, Production] ')

app = create_app(app_config)
#setup logger
logging.basicConfig(level=logging.ERROR,
                    format="%(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
Migrate(app, db) 

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)
    
if DEBUG:
    app.logger.info('DEBUG            = ' + str(DEBUG))
    app.logger.info('Page Compression = ' + ('FALSE' if DEBUG else 'TRUE'))
    app.logger.info('DBMS             = ' + app_config.SQLALCHEMY_DATABASE_URI)
    app.logger.info('ASSETS      = ' + app_config.ASSETS)

if __name__ == "__main__":
    # Run with host='0.0.0.0' to make it accessible from other devices on your network
    app.run(host='0.0.0.0', port=5001, debug=True)
