from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from rdflib import Graph

from rest_framework import viewsets
from .serializers import FileSerializer
from .models import File

import os
from .converter import process_and_save_file
from .convert_to_rdf import rdf_processing
from .combinator import combine_csv_files

# Create your views here.

class RDFFileView(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    queryset = File.objects.all()

    def create(self, request):
        rdfFile = None

        if 'rdfFile' in request.FILES:
            rdfFile = request.FILES['rdfFile']
        if 'originalFile1' in request.FILES:
            originalFile = request.FILES['originalFile1']
        if 'originalFile2' in request.FILES:
            originalFile2 = request.FILES['originalFile2']

        if request.method == 'POST' and rdfFile:
            uploaded_file = rdfFile

            # Process the file content as needed
            #file_content = uploaded_file.read().decode('utf-8')
            
            # Create a Graph instance
            g = Graph()

            # Parse your RDF ontology file (replace 'ontology.rdf' with your file)
            g.parse(uploaded_file, format='xml')

            # Iterate through the triples to extract subject, predicate, and object

            data=[]
            for subj, pred, obj in g:
                # Print the extracted triple
                #print(f"Subject: {subj}\nPredicate: {pred}\nObject: {obj}\n"
                data.append({'Subject': subj, 'Predicate': pred, 'Object': obj})

            return JsonResponse({'Data' : data})
        
        elif request.method == 'POST' and originalFile:

            file_instance = File(originalFile1=request.FILES['originalFile1'], originalFile2=request.FILES['originalFile2'])
            file_instance.save()
            for file_key in ['originalFile1', 'originalFile2']:
                process_and_save_file(file_instance=file_instance, file_key=file_key)

            # uploaded_file = originalFile
            # file_extension = os.path.splitext(uploaded_file.name)[1] 

            # file_instance = File(originalFile=uploaded_file)
            # file_instance.save()

            # if file_extension == '.json':
            #     process_and_save_file(file_instance)
            #     json_response = {'Data': 'Converted JSON!'}
            #     # return JsonResponse({'Data': 'Converted JSON!'})
            # elif file_extension == '.sql':
            #     process_and_save_file(file_instance)
            #     json_response = {'Data': 'Converted SQL!'}
            #     # return JsonResponse({'Data': 'Converted SQL!'})
            # elif file_extension == '.csv':
            #     json_response = {'Data': 'File already in CSV!'}
            #     # return JsonResponse({'Data': 'File already in CSV!'})
                
            combine_csv_files(file_instance)
            json_data = rdf_processing()
            return JsonResponse(json_data)
            
        else:
            return JsonResponse({'error': 'File not found.'})
        
def download(request):
    # Fetch the latest model instance
    file_instance = File.objects.latest('id')

    # Create a response with the rdfFile
    response = FileResponse(file_instance.rdfFile)
    response['Content-Disposition'] = f'attachment; filename="{file_instance.rdfFile.name}"'

    return response

def download_json(request):
    # Fetch the latest model instance
    file_instance = File.objects.latest('id')

    # Create a response with the jsonFile
    response = FileResponse(file_instance.jsonFile)
    response['Content-Disposition'] = f'attachment; filename="{file_instance.jsonFile.name}"'

    return response
        
""" def process_file(request, file_key, model_instance):
    if file_key in request.FILES:
        uploaded_file = request.FILES[file_key]
        file_extension = os.path.splitext(uploaded_file.name)[1] 

        if file_extension == '.json':
            processed_file = process_and_save_file(uploaded_file, file_key)
        elif file_extension == '.sql':
            processed_file = process_and_save_file(uploaded_file, file_key)
        elif file_extension == '.csv':
            processed_file = uploaded_file

        if processed_file:
            if file_key == 'originalFile1':
                model_instance.originalFile1 = processed_file
            elif file_key == 'originalFile2':
                model_instance.originalFile2 = processed_file

            model_instance.save()

            return {'Data': f'Processed and saved {file_key}!'}
    else:
        return {'error': f'File {file_key} not found.'} """