from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        identifiers = request.form['identifiers']
        assembly = request.form['assembly']
        padding_5 = request.form.get('padding_5', 0, type=int)  # Default 0 if not specified
        padding_3 = request.form.get('padding_3', 0, type=int)  # Default 0 if not specified
        results = process_identifiers(identifiers, assembly, padding_5, padding_3)
        return render_template('results.html', results=results)
    panels = fetch_panels_from_panelapp()  # Fetch panels for GET request
    return render_template('index.html', panels=panels)


def process_identifiers(identifiers, assembly, padding_5, padding_3):
    ids = identifiers.replace(',', '\n').split()
    results = []
    for identifier in ids:
        if identifier.startswith('rs'):
            # Handling rsIDs (SNPs) without padding
            result = fetch_variant_info(identifier, assembly)
            if result:
                results.append(result)
        else:
            # Handling other identifiers such as gene IDs with padding
            result = fetch_data_from_tark(identifier, assembly)
            if result:
                for r in result:
                    r['loc_start'] = max(0, r['loc_start'] - padding_5)  # Adjust start with 5' padding
                    r['loc_end'] += padding_3  # Adjust end with 3' padding
                results.extend(result)
    return results


def fetch_variant_info(rsid, assembly):
    if assembly == 'GRCh38':
        ensembl_url = f"https://rest.ensembl.org/vep/human/id/{rsid}?refseq=true&canonical=true;content-type=application/json"
    elif assembly == 'GRCh37':
        ensembl_url = f"https://grch37.rest.ensembl.org/vep/human/id/{rsid}?refseq=true&canonical=true;content-type=application/json"
    else:
        print(f"Invalid assembly: {assembly}")
        return None

    try:
        response = requests.get(ensembl_url)
        if response.status_code == 200:
            data = response.json()
            if data:
                for item in data:
                    if 'transcript_consequences' in item:
                        for consequence in item['transcript_consequences']:
                            if 'transcript_id' in consequence and consequence['transcript_id'].startswith('NM') and 'canonical' in consequence and consequence['canonical']:
                                accession = consequence['transcript_id']
                                entrez_id = consequence['gene_id']
                                gene = consequence['gene_symbol']
                                chromosome = item['seq_region_name']
                                start = item['start']
                                end = item['end']
                                return {
                                    'rsid': rsid,
                                    'accession': accession,
                                    'entrez_id': entrez_id,
                                    'gene': gene,
                                    'chromosome': chromosome,
                                    'start': start,
                                    'end': end
                                }
            else:
                print(f"No data found for rsID {rsid}")
                return None
        else:
            print(f"Failed to retrieve variant information for rsID {rsid}: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while retrieving variant information for rsID {rsid}: {e}")
        return None

def fetch_data_from_tark(identifier, assembly):
    base_url = 'https://tark.ensembl.org/api/'
    search_url = f"{base_url}transcript/search/"
    params = {
        'identifier_field': identifier,
        'expand': 'transcript_release_set,genes,exons',
    }

    try:
        print(search_url, params)
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = []
            max_version_transcript = None
            max_version = -1
            for item in data:
                if 'assembly' in item and item['assembly'] == assembly:
                    if item['stable_id'].startswith('NM'):
                        version = int(item['stable_id_version'])
                        if version > max_version:
                            max_version = version
                            max_version_transcript = item
            if max_version_transcript:
                accession = f"{max_version_transcript['stable_id']}.{max_version_transcript['stable_id_version']}"
                entrez_id = max_version_transcript['genes'][0]['stable_id'] if 'genes' in max_version_transcript and max_version_transcript['genes'] else None
                exons = max_version_transcript.get('exons', [])
                for exon in exons:
                    results.append({
                        'loc_region': exon['loc_region'],
                        'loc_start': exon['loc_start'],
                        'loc_end': exon['loc_end'],
                        'accession': accession,
                        'gene': identifier,
                        'entrez_id': entrez_id
                    })
            if results:
                return results
            else:
                print("No results found for this identifier.")
                return None
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@app.route('/panels')
def panels():
    panel_data = fetch_panels_from_panelapp()
    return render_template('index.html', panels=panel_data)

def fetch_panels_from_panelapp():
    url = "https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff/"
    panels_list = []

    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for panel in data['results']:
                if panel['relevant_disorders'] and 'R' in panel['relevant_disorders'][-1]:
                    # Assumes the 'R' code is always the last element
                    r_code = panel['relevant_disorders'][-1]
                    full_name = f"{r_code} - {panel['name']}"
                else:
                    full_name = panel['name']
                panels_list.append((panel['id'], full_name))
            url = data.get('next')  # Move to the next page if it exists
        else:
            print("Failed to fetch panels:", response.status_code)
            break  # Exit loop if there is an error

    return panels_list


@app.route('/get_genes_by_panel/<panel_id>')
def get_genes_by_panel(panel_id):
    gene_list = fetch_genes_for_panel(panel_id)
    return jsonify(gene_list=gene_list)

def fetch_genes_for_panel(panel_id):
    response = requests.get(f"https://panelapp.genomicsengland.co.uk/api/v1/panels/{panel_id}/")
    if response.status_code == 200:
        panel = response.json()
        # Filter genes to include only those with a confidence_level of '3'
        genes = [gene['gene_data']['gene_symbol'] for gene in panel['genes'] if gene['confidence_level'] == '3']
        print(genes)
        return genes
    else:
        return []

if __name__ == '__main__':
    app.run(debug=True)