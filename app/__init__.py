from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.bed_generator import bed_generator_bp
    app.register_blueprint(bed_generator_bp)

    from app.samplesheet_validator import samplesheet_validator_bp
    app.register_blueprint(samplesheet_validator_bp, url_prefix='/samplesheet_validator')

    # Register all other future blueprints here

    return app