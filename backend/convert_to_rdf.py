from .models import File
import pandas as pd
from rdflib import Graph, Literal, Namespace
from urllib.parse import quote, unquote
import csv
import os
from django.conf import settings
from django.core.files import File as DjangoFile
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .convert_from_rdf import convert_rdf_to_jsonld

def rdf_processing():

    latest_file_object = File.objects.all().order_by('id').last()

    csv_file = latest_file_object.csvFile.path #read_csv cannot handle File Object, so we need to get the path of the file.

    df = pd.read_csv(csv_file, dtype={'aadhaar_number': str, 'age': int, 'heart_rate': int, 'cholestrol': float})
    # print(df)

    df['name'] = df['first_name'] + ' ' + df['last_name']
    
    df['id'] = df['name'] + '_' + df['aadhaar_number']

    # Process 'diagnosis' column, duplicate rows for each diagnosis if multiple present.
    df['diagnosis'] = df['diagnosis'].str.split(',')
    df = df.explode('diagnosis')
    df['diagnosis'] = df['diagnosis'].str.strip()

    # Extract all unique diagnosis names
    unique_diagnoses = df['diagnosis'].unique()

    # Encode the diagnosis names
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(unique_diagnoses)

    # Calculate the similarity between each pair of diagnosis names
    similarities = cosine_similarity(embeddings)
    print("similarity:", similarities)

    most_similar_indices = np.argsort(similarities, axis=1)[:, -2] # np.argsort() returns new array which displays index of elements when sorted (i.e [2, 0, 1] will return [1(Index of 0), 2(Index of 1), 0(Index of 2)])
    print("similar:", most_similar_indices)

    second_max_similarities = np.sort(similarities, axis=1)[:, -2] # Receive the second highest similarity value for each diagnosis.
    print("max:", second_max_similarities)

    mapped_diagnoses = set()

    # If max similarity is less than 0.8, or the diagnosis has already been mapped, map the diagnosis to itself
    semantic_merge_dict = {'mapping_info': []}
    most_similar_diagnoses = []
    mapped_count = 0
    for idx, i in enumerate(most_similar_indices): #idx -> current diagnosis, i -> index of similar diagnosis
        if (second_max_similarities[idx] > 0.8 and ((unique_diagnoses[i], unique_diagnoses[idx]) and (unique_diagnoses[idx], unique_diagnoses[i]) not in mapped_diagnoses)):
            most_similar_diagnoses.append(unique_diagnoses[i])
            mapped_diagnoses.add((unique_diagnoses[i], unique_diagnoses[idx]))
            mapped_count += 1
            print("Mapped:", unique_diagnoses[idx], "to", unique_diagnoses[i])
            semantic_merge_dict['mapping_info'].append({"diagnosis1": unique_diagnoses[idx], "diagnosis2": unique_diagnoses[i]})
        else:
            most_similar_diagnoses.append(unique_diagnoses[idx])

    semantic_merge_dict.update({'mapped_count': mapped_count})

    print("Mapped Count:", mapped_count)

    # Create a mapping from each diagnosis name to its most similar diagnosis name
    diagnosis_mapping = dict(zip(unique_diagnoses, most_similar_diagnoses)) #Zip: (Disease1, Disease2) -> {Disease1: Disease2}.
    print(diagnosis_mapping)

    # Replace each diagnosis name with its most similar diagnosis name
    df['diagnosis'] = df['diagnosis'].map(diagnosis_mapping)
    print(df['diagnosis'])

    #df = df[['name', 'age', 'gender', 'blood_group', 'blood_pressure', 'cholestrol', 'heart_rate', 'disabled', 'diagnosis']]
    df = df[['id', 'name', 'age', 'gender', 'blood_group', 'blood_pressure', 'cholestrol', 'heart_rate', 'disabled', 'diagnosis']]

    df = df.rename(columns={
        'id': 'hasID',
        'name': 'hasName',
        'age': 'hasAge',
        'gender': 'hasGender',
        'blood_group': 'hasBloodGroup',
        'blood_pressure': 'hasBloodPressure',
        'cholestrol': 'hasCholestrol',
        'heart_rate': 'hasHeartRate',
        'disabled': 'isDisabled',
        'diagnosis': 'hasDiagnosis'
    })

    with open(csv_file, 'w') as file:
        df.to_csv(file, index=False)

    duplicate_count = csv_to_rdf(csv_file, 'rdf_output.rdf')

    with open('rdf_output.rdf', 'rb') as file:
        latest_file_object.rdfFile.save('rdf_output.rdf', DjangoFile(file)) #DjangoFile is alias for File() constructor, since File is already used by Model.
        latest_file_object.save()

    convert_rdf_to_jsonld(latest_file_object)


    g = Graph()
    g.parse('rdf_output.rdf', format='xml')
    triples = list(g)

    print("Triples:", triples[1])

    nodes = set()
    links = []

    # for s, p, o in triples:
    #     nodes.add(str(s))
    #     nodes.add(str(o))
    #     links.append({"source": str(s), "target": str(o), "relation": str(p)})

    links_by_source = {}

    graph_array = {}

    for s, p, o in triples:

        s_name = unquote(str(s).split('/')[-1])
        p_name = unquote(str(p).split('/')[-1])
        o_name = unquote(str(o) if isinstance(o, Literal) else str(o).split('/')[-1])
        # nodes.add(s_name)
        # nodes.add(o_name)
        # links.append({"source": s_name, "relation": p_name, "target": o_name})

        # If the source name is not already a key in the dictionary, add it with an empty list as its value
        """ if s_name not in links_by_source:
            links_by_source[s_name] = []

        # Append the link to the list of links for this source
        links_by_source[s_name].append({"source": s_name, "relation": p_name, "target": o_name})

        if s_name not in graph_array:
            graph_array[s_name] = {'nodes': [], 'links': []}

        graph_array[s_name]['nodes'].append(o_name)
        graph_array[s_name]['links'].append({"source": s_name, "target": o_name, "relation": p_name}) """

        nodes.add(s_name)
        nodes.add(o_name)
        links.append({"source": s_name, "target": o_name, "relation": p_name, })

    nodes = [{"id": node} for node in nodes] #For Graph
        
    #nodes = list(nodes)

    temp_df = pd.DataFrame(links)
    #print(temp_df)
    # temp_df = temp_df[temp_df['relation'] == 'hasGender']['target'].value_counts()
    # print("TEST", temp_df)
    # male_count = temp_df['Male']
    # female_count = temp_df['Female']

    # temp_df = temp_df[temp_df['relation'] == 'isDisabled']['target'].value_counts()
    # disabled_yes, disabled_no = temp_df['Yes'], temp_df['No']

    # temp_df = temp_df[temp_df['relation'] == 'hasBloodGroup']['target'].value_counts()
    # blood_group_A_plus, blood_group_B_plus, blood_group_AB_plus, blood_group_O_plus = temp_df['A+'], temp_df['B+'], temp_df['AB+'], temp_df['O+']
    # blood_group_A_minus, blood_group_B_minus, blood_group_AB_minus, blood_group_O_minus = temp_df['A-'], temp_df['B-'], temp_df['AB-'], temp_df['O-']
    # blood_group_dict = {"A+": blood_group_A_plus, "B+": blood_group_B_plus, "AB+": blood_group_AB_plus, "O+": blood_group_O_plus, "A-": blood_group_A_minus, "B-": blood_group_B_minus, "AB-": blood_group_AB_minus, "O-": blood_group_O_minus}

    diagnosis_dict = temp_df[temp_df['relation'] == 'hasDiagnosis']['target'].value_counts().to_dict()
    bloodgroup_dict = temp_df[temp_df['relation'] == 'hasBloodGroup']['target'].value_counts().to_dict()
    gender_dict = temp_df[temp_df['relation'] == 'hasGender']['target'].value_counts().to_dict()
    disabled_dict = temp_df[temp_df['relation'] == 'isDisabled']['target'].value_counts().to_dict()
    bloodpressure_dict = temp_df[temp_df['relation'] == 'hasBloodPressure']['target'].value_counts().to_dict()

    # avg_age = float(temp_df[temp_df['relation'] == 'hasAge']['target'].apply(int).mean())
    # min_age = float(temp_df[temp_df['relation'] == 'hasAge']['target'].apply(int).min())
    # max_age = float(temp_df[temp_df['relation'] == 'hasAge']['target'].apply(int).max())

    # avg_chol = float(temp_df[temp_df['relation'] == 'hasCholestrol']['target'].apply(float).mean())
    # min_chol = float(temp_df[temp_df['relation'] == 'hasCholestrol']['target'].apply(float).min())
    # max_chol = float(temp_df[temp_df['relation'] == 'hasCholestrol']['target'].apply(float).max())

    # avg_hr = float(temp_df[temp_df['relation'] == 'hasHeartRate']['target'].apply(int).mean())
    # min_hr = float(temp_df[temp_df['relation'] == 'hasHeartRate']['target'].apply(int).min())
    # max_hr = float(temp_df[temp_df['relation'] == 'hasHeartRate']['target'].apply(int).max())

    avg_age = round(float(temp_df[temp_df['relation'] == 'hasAge']['target'].apply(int).mean()), 2)
    min_age = round(float(temp_df[temp_df['relation'] == 'hasAge']['target'].apply(int).min()), 2)
    max_age = round(float(temp_df[temp_df['relation'] == 'hasAge']['target'].apply(int).max()), 2)

    avg_chol = round(float(temp_df[temp_df['relation'] == 'hasCholestrol']['target'].apply(float).mean()), 2) #String <-> Int, String <-> Float but Float -> Int NO
    min_chol = round(float(temp_df[temp_df['relation'] == 'hasCholestrol']['target'].apply(float).min()), 2) # So convert type from string to float and then to int.
    max_chol = round(float(temp_df[temp_df['relation'] == 'hasCholestrol']['target'].apply(float).max()), 2)

    avg_hr = round(float(temp_df[temp_df['relation'] == 'hasHeartRate']['target'].apply(float).mean()), 2)
    min_hr = round(float(temp_df[temp_df['relation'] == 'hasHeartRate']['target'].apply(float).min()), 2)
    max_hr = round(float(temp_df[temp_df['relation'] == 'hasHeartRate']['target'].apply(float).max()), 2)

    age_dict = {"avg_age": avg_age, "min_age": min_age, "max_age": max_age}
    cholestrol_dict = {"avg_chol": avg_chol, "min_chol": min_chol, "max_chol": max_chol}
    hr_dict = {"avg_hr": avg_hr, "min_hr": min_hr, "max_hr": max_hr}

    #print("Diagnosis Dict:", diagnosis_dict)
    # print(male_count, female_count)
    
    json_data = {"graph_data": {"nodes": nodes, "links": links}, "duplicate_count": duplicate_count, "entries": len(nodes), "diagnosis_dict": diagnosis_dict, "bloodgroup_dict": bloodgroup_dict, "bloodpressure_dict": bloodpressure_dict, "gender_dict": gender_dict, "divyang_dict": disabled_dict, "age_dict": age_dict, "cholestrol_dict": cholestrol_dict, "hr_dict": hr_dict, "semantic_merge_dict": semantic_merge_dict}

    # json_data = {"graph_data": {"nodes": nodes, "links": links}, "duplicate_count": duplicate_count, "entries": len(nodes), "diagnosis_dict": diagnosis_dict, "bloodgroup_dict": bloodgroup_dict, "bloodpressure_dict": bloodpressure_dict, "gender_dict": gender_dict, "divyang_dict": disabled_dict, "age_dict": age_dict}
    
    #print(json_data)
    #json_data = graph_array
    return json_data

# Load CSV data and convert to RDF triples
def csv_to_rdf(csv_file, output_file):

    ontology_file_path = os.path.join(settings.BASE_DIR, 'backend', 'ontology.ttl')

    g = Graph()
    g.parse(ontology_file_path, format="turtle")

    # Define namespaces
    ex = Namespace("http://example.org/")

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        #
        duplicate_count = 0
        uri_list = []
        #
        for row in reader:
            safe_id = quote(row['hasID'])  # URL encode the name
            subject_uri = ex[safe_id]  # Example: http://example.org/JohnDoe

            #
            if safe_id in uri_list:
                duplicate_count += 1    
            else:
                uri_list.append(safe_id)
            #

            for key, value in row.items():
                property_uri = ex[key]
                if key == "hasID":
                    continue

                # if key == 'hasDiagnosis':
                #     # Split the 'hasDiagnosis' string into individual diseases and add each as a 'hasDiagnosis' property
                #     diseases = value.split(',')
                #     for disease in diseases:
                #         g.add((subject_uri, property_uri, Literal(disease.strip())))
                # else:
                #     g.add((subject_uri, property_uri, Literal(value)))

                g.add((subject_uri, property_uri, Literal(value)))  

    # Serialize RDF graph to RDF/XML format
    print(f"Duplicate count: {duplicate_count}")
    g.serialize(destination=output_file, format='xml')
    
    return duplicate_count

        




