from flask import render_template, request, jsonify
from app.bed_generator import bed_generator_bp
from app.bed_generator.utils import process_identifiers, fetch_panels_from_panelapp, fetch_genes_for_panel

@bed_generator_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        identifiers = request.form['identifiers']
        assembly = request.form['assembly']
        padding_5 = request.form.get('padding_5', 0, type=int)
        padding_3 = request.form.get('padding_3', 0, type=int)
        results = process_identifiers(identifiers, assembly, padding_5, padding_3)
        return render_template('results.html', results=results)
    panels = fetch_panels_from_panelapp()
    return render_template('bed_generator.html', panels=panels)

@bed_generator_bp.route('/panels')
def panels():
    panel_data = fetch_panels_from_panelapp()
    return render_template('bed_generator.html', panels=panel_data)

@bed_generator_bp.route('/get_genes_by_panel/<panel_id>')
def get_genes_by_panel(panel_id):
    include_amber = request.args.get('include_amber', 'false') == 'true'
    include_red = request.args.get('include_red', 'false') == 'true'
    gene_list = fetch_genes_for_panel(panel_id, include_amber, include_red)
    return jsonify(gene_list=gene_list)