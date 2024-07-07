from flask import render_template, request, jsonify, redirect, url_for, session
from app.bed_generator import bed_generator_bp
from app.bed_generator.utils import process_identifiers, fetch_panels_from_panelapp, fetch_genes_for_panel, get_panels_from_db, store_panels_in_db

@bed_generator_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        identifiers = request.form['identifiers']
        coordinates = request.form['coordinates']
        assembly = request.form['assembly']
        padding_5 = request.form.get('padding_5', 0, type=int)
        padding_3 = request.form.get('padding_3', 0, type=int)
        
        try:
            results = []
            # Process identifiers (genes, rsIDs) only once
            if identifiers.strip():
                results.extend(process_identifiers(identifiers, '', assembly, padding_5, padding_3))
            
            # Process each coordinate separately
            coordinate_list = [coord.strip() for coord in coordinates.split('\n') if coord.strip()]
            for coord in coordinate_list:
                results.extend(process_identifiers('', coord, assembly, padding_5, padding_3))
            
            session['results'] = results
            return redirect(url_for('bed_generator.results'))
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    panels = get_panels_from_db()
    return render_template('bed_generator.html', panels=panels)

@bed_generator_bp.route('/results')
def results():
    results = session.get('results', [])
    return render_template('results.html', results=results)

@bed_generator_bp.route('/panels')
def panels():
    panel_data = get_panels_from_db()
    return jsonify(panel_data)

@bed_generator_bp.route('/refresh_panels')
def refresh_panels():
    panel_data = fetch_panels_from_panelapp()
    store_panels_in_db(panel_data)
    updated_panel_data = get_panels_from_db()
    return jsonify(updated_panel_data)

@bed_generator_bp.route('/get_genes_by_panel/<panel_id>')
def get_genes_by_panel(panel_id):
    include_amber = request.args.get('include_amber', 'false') == 'true'
    include_red = request.args.get('include_red', 'false') == 'true'
    gene_list = fetch_genes_for_panel(panel_id, include_amber, include_red)
    return jsonify(gene_list=gene_list)