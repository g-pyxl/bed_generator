from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        identifiers = request.form['identifiers']
        assembly = request.form['assembly']
        results = process_identifiers(identifiers, assembly)
        return render_template('results.html', results=results)
    return render_template('index.html')

def process_identifiers(identifiers, assembly):
    ids = identifiers.replace(',', '\n').split()
    results = []
    for identifier in ids:
        if identifier.startswith('rs'):
            result = fetch_variant_info(identifier, assembly)
            if result:
                results.append(result)
        else:
            result = fetch_data_from_tark(identifier, assembly)
            if result:
                results.extend(result)
    return results

def fetch_variant_info(rsid, assembly):
    if assembly == 'GRCh38':
        ensembl_url = f"https://rest.ensembl.org/variation/human/{rsid}?content-type=application/json"
    elif assembly == 'GRCh37':
        ensembl_url = f"https://grch37.rest.ensembl.org/variation/human/{rsid}?content-type=application/json"
    else:
        print(f"Invalid assembly: {assembly}")
        return None

    try:
        response = requests.get(ensembl_url)
        if response.status_code == 200:
            data = response.json()
            if data:
                mappings = data['mappings']
                for mapping in mappings:
                    if mapping['assembly_name'] == assembly:
                        chrom = mapping['seq_region_name']
                        start = mapping['start']
                        end = mapping['end']
                        return {
                            'rsid': rsid,
                            'chromosome': chrom,
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
            print(data)
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
                exons = max_version_transcript.get('exons', [])
                exon_info = []
                for exon in exons:
                    exon_info.append({
                        'exon_id': exon['exon_id'],
                        'stable_id': exon['stable_id'],
                        'stable_id_version': exon['stable_id_version'],
                        'assembly': exon['assembly'],
                        'loc_start': exon['loc_start'],
                        'loc_end': exon['loc_end'],
                        'loc_strand': exon['loc_strand'],
                        'loc_region': exon['loc_region'],
                        'loc_checksum': exon['loc_checksum'],
                        'exon_checksum': exon['exon_checksum'],
                        'exon_order': exon['exon_order']
                    })
                return [{
                    'stable_id': max_version_transcript['stable_id'],
                    'exons': exon_info
                }]
            else:
                print("No results found for this identifier.")
                return None
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
if __name__ == '__main__':
    app.run(debug=True)