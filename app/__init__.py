from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.bed_generator import bed_generator_bp
    app.register_blueprint(bed_generator_bp)

    # Register all other future blueprints here

    return app