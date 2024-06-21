# import csv
# from io import StringIO
# from seglh_naming.sample import Sample
# from seglh_naming.samplesheet import Samplesheet

# def validate_samplesheet(file):
#     # Read the uploaded file
#     file_contents = file.read().decode('utf-8')
#     csv_data = csv.DictReader(StringIO(file_contents))

#     # Initialize variables
#     errors = []
#     samples = []

#     # Perform validation checks
#     try:
#         samplesheet_obj = Samplesheet.from_string(file.filename)
#     except ValueError as exception:
#         errors.append(f"Samplesheet name invalid: {str(exception)}")
#     else:
#         # Check sequencer ID
#         if samplesheet_obj.sequencerid not in ["A01229", "NB551068"]:  # Replace with your valid sequencer IDs
#             errors.append(f"Sequencer ID invalid: {samplesheet_obj.sequencerid}")

#     for row in csv_data:
#         sample_id = row.get("Sample_ID")
#         sample_name = row.get("Sample_Name")

#         if sample_id and sample_name:
#             samples.append((sample_id, sample_name))

#             # Check sample names using seglh_naming
#             try:
#                 sample_obj_id = Sample.from_string(sample_id)
#                 sample_obj_name = Sample.from_string(sample_name)
#             except ValueError as exception:
#                 errors.append(str(exception))
#             else:
#                 # Check panel numbers
#                 panel_numbers = [sample_obj_id.panelnumber, sample_obj_name.panelnumber]
#                 for panel_number in panel_numbers:
#                     if panel_number not in ["Pan5085", "Pan5112", "Pan5114"]:  # Replace with your valid panel numbers
#                         errors.append(f"Panel number invalid: {panel_number}")

#     # Check if sample IDs and names match
#     sample_ids = [sample[0] for sample in samples]
#     sample_names = [sample[1] for sample in samples]
#     if len(sample_ids) != len(set(sample_ids)) or len(sample_names) != len(set(sample_names)):
#         errors.append("Sample IDs and names do not match")

#     # Check for TSO panels
#     tso_panels = ["Pan2835", "Pan3142"]  # Replace with your TSO panel numbers
#     tso = any(sample[0].startswith("TSO") or sample[1].startswith("TSO") for sample in samples)
#     if tso and not any(panel in tso_panels for panel in panel_numbers):
#         errors.append("TSO panel not found for TSO samples")

#     # Check for development panels
#     dev_panel = "Pan9999"  # Replace with your development panel number
#     dev_run = any(dev_panel in sample for sample in samples)

#     # Return the validation results
#     return {'errors': errors, 'tso': tso, 'dev_run': dev_run}