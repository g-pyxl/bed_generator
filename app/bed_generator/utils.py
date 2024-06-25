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
        CREATE TABLE IF NOT EXISTS transcripts (
            transcript_id TEXT PRIMARY KEY,
            stable_id TEXT NOT NULL,
            stable_id_version INTEGER,
            assembly TEXT,
            loc_start INTEGER,
            loc_end INTEGER,
            loc_strand INTEGER,
            loc_region TEXT,
            loc_checksum TEXT,
            transcript_checksum TEXT,
            biotype TEXT,
            sequence TEXT,
            gene_id TEXT,
            three_prime_utr_start INTEGER,
            three_prime_utr_end INTEGER,
            three_prime_utr_seq TEXT,
            three_prime_utr_checksum TEXT,
            five_prime_utr_start INTEGER,
            five_prime_utr_end INTEGER,
            five_prime_utr_seq TEXT,
            five_prime_utr_checksum TEXT,
            mane_transcript TEXT,
            mane_transcript_type TEXT,
            FOREIGN KEY(gene_id) REFERENCES genes(gene_id)
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exons (
            exon_id INTEGER PRIMARY KEY,
            stable_id TEXT NOT NULL,
            stable_id_version INTEGER,
            assembly TEXT,
            loc_start INTEGER,
            loc_end INTEGER,
            loc_strand INTEGER,
            loc_region TEXT,
            loc_checksum TEXT,
            exon_checksum TEXT,
            transcript_id TEXT,
            exon_order INTEGER,
            FOREIGN KEY(transcript_id) REFERENCES transcripts(transcript_id)
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcript_release_set (
            release_set_id INTEGER PRIMARY KEY AUTOINCREMENT,
            assembly TEXT,
            shortname TEXT,
            description TEXT,
            release_date TEXT,
            source TEXT,
            transcript_id TEXT,
            FOREIGN KEY(transcript_id) REFERENCES transcripts(transcript_id)
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

def store_transcript_data(conn, data):
    cursor = conn.cursor()

    # Loop through each transcript entry in the data
    for entry in data:
        # Generate transcript_id
        transcript_id = f"{entry['stable_id']}.{entry['stable_id_version']}"

        # Insert gene information
        if 'genes' in entry:
            for gene in entry['genes']:
                cursor.execute('''
                    INSERT OR IGNORE INTO genes (gene_id, stable_id, stable_id_version, assembly, loc_start, loc_end, loc_strand, loc_region, loc_checksum, name, gene_checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                ''', (
                    gene['stable_id'] + '.' + str(gene['stable_id_version']),
                    gene['stable_id'],
                    gene['stable_id_version'],
                    gene['assembly'],
                    gene['loc_start'],
                    gene['loc_end'],
                    gene['loc_strand'],
                    gene['loc_region'],
                    gene['loc_checksum'],
                    gene.get('name', None),
                    gene['gene_checksum']
                ))

        # Insert transcript information
        cursor.execute('''
            INSERT OR IGNORE INTO transcripts (
                transcript_id, stable_id, stable_id_version, assembly, loc_start, loc_end, loc_strand, loc_region, loc_checksum, transcript_checksum, biotype, sequence, gene_id,
                three_prime_utr_start, three_prime_utr_end, three_prime_utr_seq, three_prime_utr_checksum, five_prime_utr_start, five_prime_utr_end, five_prime_utr_seq, five_prime_utr_checksum,
                mane_transcript, mane_transcript_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', (
            transcript_id,
            entry['stable_id'],
            entry['stable_id_version'],
            entry['assembly'],
            entry['loc_start'],
            entry['loc_end'],
            entry['loc_strand'],
            entry['loc_region'],
            entry['loc_checksum'],
            entry['transcript_checksum'],
            entry['biotype'],
            entry['sequence'],
            entry['genes'][0]['stable_id'] + '.' + str(entry['genes'][0]['stable_id_version']) if 'genes' in entry and entry['genes'] else None,
            entry.get('three_prime_utr_start', None),
            entry.get('three_prime_utr_end', None),
            entry.get('three_prime_utr_seq', None),
            entry.get('three_prime_utr_checksum', None),
            entry.get('five_prime_utr_start', None),
            entry.get('five_prime_utr_end', None),
            entry.get('five_prime_utr_seq', None),
            entry.get('five_prime_utr_checksum', None),
            entry.get('mane_transcript', None),
            entry.get('mane_transcript_type', None)
        ))

        # Warning if MANE PLUS CLINICAL is found
        if entry.get('mane_transcript_type') == 'MANE PLUS CLINICAL':
            print(f"Warning: Transcript {transcript_id} has MANE PLUS CLINICAL type.")

        # Insert exons information
        if 'exons' in entry:
            for exon in entry['exons']:
                cursor.execute('''
                    INSERT OR IGNORE INTO exons (exon_id, stable_id, stable_id_version, assembly, loc_start, loc_end, loc_strand, loc_region, loc_checksum, exon_checksum, transcript_id, exon_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                ''', (
                    exon['exon_id'],
                    exon['stable_id'],
                    exon['stable_id_version'],
                    exon['assembly'],
                    exon['loc_start'],
                    exon['loc_end'],
                    exon['loc_strand'],
                    exon['loc_region'],
                    exon['loc_checksum'],
                    exon['exon_checksum'],
                    transcript_id,
                    exon['exon_order']
                ))

        # Insert transcript release set information
        if 'transcript_release_set' in entry:
            for release_set in entry['transcript_release_set']:
                cursor.execute('''
                    INSERT INTO transcript_release_set (assembly, shortname, description, release_date, source, transcript_id)
                    VALUES (?, ?, ?, ?, ?, ?);
                ''', (
                    release_set['assembly'],
                    release_set['shortname'],
                    release_set['description'],
                    release_set['release_date'],
                    release_set['source'],
                    transcript_id
                ))

    conn.commit()

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
        
        cursor.execute('SELECT gene_symbol, confidence_level FROM panel_genes WHERE panel_id = ?', (panel_id,))
        genes = cursor.fetchall()
        
        if relevant_disorders:
            r_code = relevant_disorders.split(',')[-1]
            full_name = f"{r_code} - {name}"
        else:
            full_name = name
        
        panel_data.append({
            'panel_id': panel_id,
            'name': full_name,
            'last_updated': last_updated,
            'genes': [{'gene_symbol': gene[0], 'confidence_level': gene[1]} for gene in genes]
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
    conn = connect_db()
    cursor = conn.cursor()
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
            # Handling other identifiers such as gene IDs with padding
            cursor.execute("SELECT stable_id FROM genes WHERE name = ? AND assembly = ?", (identifier, assembly))
            gene_entry = cursor.fetchone()
            if gene_entry:
                stable_id = gene_entry[0]
                print(f"{identifier} located in database, stable_id: {stable_id}")
                
                # Retrieve the MANE transcript for the gene using stable_id and assembly
                cursor.execute("""
                    SELECT t.transcript_id, t.stable_id, t.stable_id_version
                    FROM transcripts t
                    JOIN genes g ON t.gene_id = g.gene_id
                    WHERE g.stable_id = ? AND t.assembly = ? AND t.mane_transcript_type = 'MANE SELECT'
                    ORDER BY t.stable_id_version DESC
                    LIMIT 1
                """, (stable_id, assembly))
                
                mane_transcript = cursor.fetchone()
                
                if mane_transcript:
                    transcript_id, stable_id, stable_id_version = mane_transcript
                    print(f"MANE transcript for gene {identifier}: {stable_id}.{stable_id_version}")
                    
                    # Retrieve exons for the MANE transcript
                    cursor.execute("""
                        SELECT e.loc_region, e.stable_id, e.loc_start, e.loc_end, e.exon_order
                        FROM exons e
                        WHERE e.transcript_id = ? AND e.assembly = ?
                        ORDER BY e.exon_order
                    """, (transcript_id, assembly))
                    
                    exons = cursor.fetchall()
                    if exons:
                        print(f"Exons for MANE transcript {stable_id}.{stable_id_version}:")
                        for exon in exons:
                            loc_region, exon_stable_id, loc_start, loc_end, exon_order = exon
                            print(f"  Exon {exon_order}: {exon_stable_id} ({loc_start}-{loc_end})")
                            results.append({
                                'loc_region': loc_region,
                                'loc_start': max(0, loc_start - padding_5),
                                'loc_end': loc_end + padding_3,
                                'accession': f"{stable_id}.{stable_id_version}",
                                'gene': identifier,
                                'entrez_id': stable_id
                            })
                    else:
                        print(f"No exons found for MANE transcript {stable_id}.{stable_id_version}")
                else:
                    print(f"No MANE transcript found for gene {identifier} in assembly {assembly}")
                    result = fetch_data_from_tark(identifier, assembly)
                    if result:
                        for r in result:
                            r['loc_start'] = max(0, r['loc_start'] - padding_5)
                            r['loc_end'] += padding_3
                        results.extend(result)
            else:
                print(f"{identifier} not found in the database for assembly {assembly}.")
    conn.close()
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
            # Update DB
            print("Storing in db...")
            conn = connect_db()
            store_transcript_data(conn, data)
            conn.close()
            # Process json
            results = []
            max_version_transcript = None
            max_version = -1
            for item in data:
                print(item.get('mane_transcript_type'))
                # Begin API call
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
        return []