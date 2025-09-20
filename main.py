# Main entry point for the Flask chatbot platform
import os
from app import app
import routes  # noqa: F401

if __name__ == "__main__":
    # Only enable debug in development
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)