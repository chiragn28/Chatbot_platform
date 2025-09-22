import os
from dotenv import load_dotenv

load_dotenv()  # This loads variables from .env file

from app import app
import routes  # noqa: F401
import auth_web_routes  # noqa: F401  <-- ADD THIS LINE

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
