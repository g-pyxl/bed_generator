from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key' # Default for debug, use system secret key in production

    from app.bed_generator import bed_generator_bp
    app.register_blueprint(bed_generator_bp, url_prefix='/bed_generator')

    from app.samplesheet_validator import samplesheet_validator_bp
    app.register_blueprint(samplesheet_validator_bp, url_prefix='/samplesheet_validator')

    return app