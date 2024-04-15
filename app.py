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
        result = fetch_data_from_tark(identifier, assembly)
        if result:
            results.extend(result)
    return results

def fetch_data_from_tark(identifier, assembly):
    if identifier.startswith('rs'):
        # Convert rsID to HGVS identifier using Ensembl REST API
        hgvs_identifier = convert_rsid_to_hgvs(identifier)
        if not hgvs_identifier:
            print(f"Failed to convert rsID {identifier} to HGVS identifier.")
            return None
    else:
        hgvs_identifier = identifier

    base_url = 'https://tark.ensembl.org/api/'
    search_url = f"{base_url}transcript/search/"
    params = {
        'identifier_field': hgvs_identifier,
        'expand': 'transcript_release_set,genes,exons',
    }

    try:
        print(search_url, params)
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            print(data)
            results = []
            for item in data:
                if 'assembly' in item and item['assembly'] == assembly:
                    if 'mane_transcript' in item and item['mane_transcript'].startswith('NM'):
                        exons = item.get('exons', [])
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
                        if exon_info:
                            results.append({
                                'mane_transcript': item['mane_transcript'],
                                'exons': exon_info
                            })
            if results:
                return results
            else:
                print("No MANE Select results found for this identifier.")
                return None
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def convert_rsid_to_hgvs(rsid):
    ensembl_url = f"https://rest.ensembl.org/variant_recoder/human/{rsid}"
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(ensembl_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                hgvsc_identifier = data[0]['G']['hgvsc'][0]  # Extract the first HGVS identifier from the 'G' allele
                transcript_id = hgvsc_identifier.split(".")[0]  # Extract the transcript ID from the HGVS identifier
                return transcript_id
            else:
                print(f"No data found for rsID {rsid}")
                return None
        else:
            print(f"Failed to retrieve HGVS identifiers for rsID {rsid}: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while converting rsID {rsid} to HGVS identifiers: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)