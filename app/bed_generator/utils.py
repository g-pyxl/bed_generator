import requests
import sqlite3
import datetime
import os
import json
import re

def connect_db():
    conn = sqlite3.connect('transcript.db')
    cursor = conn.cursor()
    # Create tables if they do not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genes (
            gene_id TEXT PRIMARY KEY,
            stable_id TEXT NOT NULL,
            stable_id_version INTEGER,
            assembly TEXT,
            loc_start INTEGER,
            loc_end INTEGER,
            loc_strand INTEGER,
            loc_region TEXT,
            loc_checksum TEXT,
            name TEXT,
            gene_checksum TEXT
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS panels (
            panel_id INTEGER PRIMARY KEY,
            name TEXT,
            disease_group TEXT,
            disease_sub_group TEXT,
            version TEXT,
            version_created TEXT,
            relevant_disorders TEXT,
            last_updated TEXT
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS panel_genes (
            panel_id INTEGER,
            gene_symbol TEXT,
            confidence_level TEXT,
            PRIMARY KEY (panel_id, gene_symbol),
            FOREIGN KEY (panel_id) REFERENCES panels (panel_id)
        );
    ''')
    conn.commit()
    return conn

def store_panels_in_db(panels_data):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM panels')
    cursor.execute('DELETE FROM panel_genes')
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for panel in panels_data:
        panel_id = panel['id']
        name = panel['name']
        disease_group = panel.get('disease_group', '')
        disease_sub_group = panel.get('disease_sub_group', '')
        version = panel['version']
        version_created = panel['version_created']
        relevant_disorders = ','.join(panel.get('relevant_disorders', []))
        
        cursor.execute('''
            INSERT INTO panels (panel_id, name, disease_group, disease_sub_group, version, version_created, relevant_disorders, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (panel_id, name, disease_group, disease_sub_group, version, version_created, relevant_disorders, timestamp))
        
        for gene in panel.get('genes', []):
            gene_symbol = gene['entity_name']
            confidence_level = gene['confidence_level']
            
            cursor.execute('''
                INSERT INTO panel_genes (panel_id, gene_symbol, confidence_level)
                VALUES (?, ?, ?)
            ''', (panel_id, gene_symbol, confidence_level))
    
    conn.commit()
    conn.close()

def get_panels_from_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT panel_id, name, disease_group, disease_sub_group, relevant_disorders, last_updated FROM panels')
    panels = cursor.fetchall()
    
    panel_data = []
    for panel in panels:
        panel_id, name, disease_group, disease_sub_group, relevant_disorders, last_updated = panel
        
        if relevant_disorders:
            r_code = relevant_disorders.split(',')[-1]
            full_name = f"{r_code} - {name}"
        else:
            full_name = name
        
        panel_data.append({
            'panel_id': panel_id,
            'name': full_name,
            'last_updated': last_updated
        })
    
    conn.close()
    
    return panel_data

def validate_coordinates(coordinates):
    regex = r'^(chr)?([1-9]|1\d|2[0-3]):(\d+)-(\d+)$'
    match = re.match(regex, coordinates, re.IGNORECASE)
    
    if not match:
        return "Invalid format. Use 'chromosome:start-end' (e.g., 1:200-300 or chr1:200-300)."
    
    chromosome, start, end = match.group(2), int(match.group(3)), int(match.group(4))
    
    if start >= end:
        return "Start position must be less than end position."
    
    return None  # No error

def process_identifiers(identifiers, coordinates, assembly, padding_5, padding_3):
    ids = identifiers.replace(',', '\n').split()
    results = []
    
    # Process genomic coordinates
    if coordinates:
        error = validate_coordinates(coordinates)
        if error:
            raise ValueError(error)
        
        coord_parts = coordinates.split(':')
        chrom = coord_parts[0].lstrip('chr')  # Remove 'chr' if present
        start, end = map(int, coord_parts[1].split('-'))
        results.append({
            'loc_region': chrom,
            'loc_start': start,
            'loc_end': end,
            'accession': 'custom',
            'gene': 'custom',
            'entrez_id': 'custom'
        })
    
    # Process other identifiers
    for identifier in ids:
        if identifier.startswith('rs'):
            # Handling rsIDs (SNPs) without padding
            result = fetch_variant_info(identifier, assembly)
            if result:
                results.append(result)
        else:
            result = fetch_data_from_tark(identifier, assembly)
            if result:
                for r in result:
                    r['loc_start'] = max(0, r['loc_start'] - padding_5)
                    r['loc_end'] += padding_3
                results.extend(result)
            else:
                print(f"No data found for {identifier} from TARK API.")

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
        'assembly': assembly
    }

    try:
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data:
                print(f"No data found for {identifier} in TARK API.")
                return None
            
            results = []
            max_version_transcript = None
            max_version = -1
            for item in data:
                if item['stable_id'].startswith('NM'):
                    version = int(item['stable_id_version'])
                    if version > max_version:
                        max_version = version
                        max_version_transcript = item

            if max_version_transcript:
                accession = f"{max_version_transcript['stable_id']}.{max_version_transcript['stable_id_version']}"
                entrez_id = max_version_transcript['genes'][0]['stable_id'] if 'genes' in max_version_transcript and max_version_transcript['genes'] else None
                gene_name = max_version_transcript['genes'][0]['name'] if 'genes' in max_version_transcript and max_version_transcript['genes'] else identifier
                exons = max_version_transcript.get('exons', [])
                for index, exon in enumerate(exons, start=1):
                    results.append({
                        'loc_region': exon['loc_region'],
                        'loc_start': exon['loc_start'],
                        'loc_end': exon['loc_end'],
                        'accession': accession,
                        'gene': gene_name,
                        'entrez_id': entrez_id,
                        'exon_id': exon['stable_id'],
                        'exon_number': index,
                        'transcript_biotype': max_version_transcript.get('biotype', ''),
                        'mane_transcript': max_version_transcript.get('mane_transcript', ''),
                        'mane_transcript_type': max_version_transcript.get('mane_transcript_type', '')
                    })

            return results
        else:
            print(f"Failed to retrieve data from TARK API: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching data from TARK API: {e}")
        return None

def fetch_panels_from_panelapp():
    url = "https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff/"
    panels_list = []

    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for panel in data['results']:
                panel_data = {
                    'id': panel['id'],
                    'name': panel['name'],
                    'disease_group': panel.get('disease_group', ''),
                    'disease_sub_group': panel.get('disease_sub_group', ''),
                    'relevant_disorders': panel.get('relevant_disorders', []),
                    'version': panel['version'],
                    'version_created': panel['version_created']
                }
                panels_list.append(panel_data)
            url = data.get('next')  # Move to the next page if it exists
        else:
            print("Failed to fetch panels:", response.status_code)
            break  # Exit loop if there is an error

    return panels_list

def fetch_genes_for_panel(panel_id, include_amber, include_red):
    response = requests.get(f"https://panelapp.genomicsengland.co.uk/api/v1/panels/{panel_id}/")
    if response.status_code == 200:
        panel = response.json()
        confidence_levels = ['3']
        if include_amber:
            confidence_levels.append('2')
        if include_red:
            confidence_levels.append('1')
        genes = [{'symbol': gene['gene_data']['gene_symbol'], 'confidence': gene['confidence_level']} for gene in panel['genes'] if gene['confidence_level'] in confidence_levels]
        return genes
    else:
        print(f"Failed to fetch genes for panel {panel_id}: {response.status_code}")
        return []
