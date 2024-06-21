from flask import Flask
from flask_session import Session

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a real secret key
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

    from .bed_generator import bed_generator_bp
    app.register_blueprint(bed_generator_bp, url_prefix='/bed_generator')

    return app