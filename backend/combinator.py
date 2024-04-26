import pandas as pd
from django.core.files import File

def combine_csv_files(file_instance):

    df1 = pd.read_csv(file_instance.originalFile1.path, dtype={'id': int, 'aadhaar_number': str, 'age': int})
    df2 = pd.read_csv(file_instance.originalFile2.path, dtype={'id': int, 'aadhaar_number': str, 'age': int})

    # df1['aadhaar_number']=df1['aadhaar_number'].astype(str)
    # df2['aadhaar_number']=df2['aadhaar_number'].astype(str)
    # #df1['age']=df1['age'].astype(int)

    # df1['aadhaar_number'] = df1['aadhaar_number'].str.replace("'", '')
    # df2['aadhaar_number'] = df2['aadhaar_number'].str.replace("'", '')

    combined_df = pd.concat([df1, df2])

    #combined_df.reset_index(drop=True, inplace=True)

    #combined_df = combined_df.dropna() CANT DO NOW, DO IN RDF CONVERTER!    

    # # Remove duplicate rows
    # combined_df = combined_df.drop_duplicates()

    # Save the combined CSV data to a new file
    combined_file_path = 'combined_file.csv'
    combined_df.to_csv(combined_file_path, index=False)

    with open(combined_file_path, 'r') as combined_file:
        # Save the combined file in the csvFile field of the model instance
        file_instance.csvFile.save('combined_file.csv', File(combined_file), save=True)