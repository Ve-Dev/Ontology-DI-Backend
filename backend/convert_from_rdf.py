from rdflib import Graph
from django.core.files import File
import json

def convert_rdf_to_jsonld(file_instance): # Convert RDF to JSON-LD (JSON format for Linked Data)
    g = Graph()
    g.parse(file_instance.rdfFile.path, format="xml")

    # Serialize as JSON-LD
    jsonld_data = g.serialize(format='json-ld', indent=4).encode('utf-8')

    # convert_jsonld_to_standard_json(jsonld_data)

    jsonld_file_path = 'jsonld_file.json'

    # Write to a file
    with open(jsonld_file_path, 'wb') as f:
        f.write(jsonld_data)
    
    with open(jsonld_file_path, 'rb') as f:
        file_instance.jsonFile.save('jsonld_file.json', File(f))

    file_instance.save()

# def convert_jsonld_to_standard_json(jsonld_data):
#     json_data = []
#     for item in jsonld_data:
#         new_item = {}
#         new_item['id'] = item['@id'].split('/')[-1]  # Get the part after the last '/'
#         for key, value in item.items():
#             if key == '@id':
#                 continue
#             new_key = key.split('/')[-1]  # Get the part after the last '/'
#             new_value = value[0]['@value']
#             new_item[new_key] = new_value
#         json_data.append(new_item)
#     return json_data