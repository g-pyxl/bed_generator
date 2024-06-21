# from flask import render_template, request
# from app.samplesheet_validator import samplesheet_validator_bp
# from app.samplesheet_validator.utils import validate_samplesheet

# @samplesheet_validator_bp.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         file = request.files['file']
#         if file:
#             results = validate_samplesheet(file)
#             return render_template('samplesheet_validator.html', results=results)
#     return render_template('samplesheet_validator.html')