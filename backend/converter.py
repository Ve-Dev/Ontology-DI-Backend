from django.core.files.base import ContentFile
from io import StringIO
import mysql.connector
import json
import csv
import os

def execute_sql_file_and_export_to_csv(sql_file_path, username, password, database, csv_file_path, host='localhost'):
    connection_params = {
        'host': host,
        'user': username,
        'password': password,
        'database': database
    }

    connection = None
    cursor = None

    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()

        # Read the SQL file
        with open(sql_file_path, 'r') as sql_file:
            sql_commands = sql_file.read().split(';')

        # Execute each SQL command
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)

        # Fetch data from the last SELECT command
        rows = cursor.fetchall()

        if rows:
            # Write data to CSV file

            output = StringIO()
            csv_writer = csv.writer(output)
            
            # Write header
            header = [description[0] for description in cursor.description]
            csv_writer.writerow(header)

            # Write rows
            csv_writer.writerows(rows)

            # Return CSV data as a string
            print(f"Data converted to CSV format: {csv_file_path}")

            return output.getvalue()
            
        else:
            print(f"No data found.")
            return None

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

""" ******************************************************************************************************************** """

def json_to_csv(input_file):
    with open(input_file, 'r') as json_file:
        data = json.load(json_file)

    # Create a StringIO object
    csv_io = StringIO()

    # Create a CSV writer object
    csv_writer = csv.writer(csv_io, lineterminator='\n')

    # Write the header using the keys of the first JSON object
    csv_writer.writerow(data[0].keys())

    # Write the data to the CSV file
    # for item in data:
    #     csv_writer.writerow(item.values())

    # Write the data to the CSV file
    for item in data:
        # Convert array data to comma-separated strings
        for key, value in item.items():
            if isinstance(value, list):
                item[key] = ', '.join(value)
        csv_writer.writerow(item.values())

    # Get the CSV data as a string
    csv_data = csv_io.getvalue()

    return csv_data

def process_and_save_file(file_instance, file_key):

    file = None
    if file_key == 'originalFile1':
        file = file_instance.originalFile1
    elif file_key == 'originalFile2':
        file = file_instance.originalFile2

    file_extension = os.path.splitext(file.name)[1]

    # Process the originalFile into a CSV file
    # csv_data = json_to_csv(file_instance.originalFile.path)

    if file_extension != '.csv':
        if file_extension == '.json':
            # Process the originalFile into a CSV file
            csv_data = json_to_csv(file.path)
        elif file_extension == '.sql':
            # Execute the SQL file and export the results to a CSV file
            csv_data = execute_sql_file_and_export_to_csv(file.path, 'root', 'data9564sql', 'sqlfile', 'output.csv')

        # Create a ContentFile from the CSV data
        csv_file = ContentFile(csv_data)

        # Overwrite the originalFile with the processed CSV file
        # file_instance.originalFile.save('output.csv', csv_file)
        if file_key == 'originalFile1':
            file_instance.originalFile1.save('output.csv', csv_file)
        elif file_key == 'originalFile2':
            file_instance.originalFile2.save('output.csv', csv_file)

        # Save the changes to the database
        file_instance.save()

""" def export_table_to_csv(username, password, database, table_name, csv_file_path, host='localhost'):
    connection_params = {
        'host': host,
        'user': username,
        'password': password,
        'database': database
    }

    connection = None
    cursor = None

    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()

        # Fetch data from the table
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()

        if rows:
            # Write data to CSV file
            with open(csv_file_path, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                
                # Write header
                header = [description[0] for description in cursor.description]
                csv_writer.writerow(header)

                # Write rows
                csv_writer.writerows(rows)

            print(f"Data exported to CSV file: {csv_file_path}")
        else:
            print(f"No data found in '{table_name}'.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
 """
# Example usage
# mysql_username = ''  #username of mysql
# mysql_password = ''#password for mysql
# mysql_database = 'project'
# table_name_to_export = 'user_details'
# csv_file_path_to_create = 'user_details.csv'

#export_table_to_csv(mysql_username, mysql_password, mysql_database, table_name_to_export, csv_file_path_to_create)

# def json_to_csv(input_file):
#     with open(input_file, 'r') as json_file:
#         data = json.load(json_file)

# # Specify the CSV file name
#     csv_file_name = 'output.csv'

#     # Open the CSV file for writing
#     with open(csv_file_name, 'w', newline='') as csv_file:
#         # Create a CSV writer object
#         csv_writer = csv.writer(csv_file)

#         # Write the header using the keys of the first JSON object
#         csv_writer.writerow(data[0].keys())

#         # Write the data to the CSV file
#         for item in data:
#             csv_writer.writerow(item.values())

#     print(f'Conversion complete. CSV file saved as {csv_file_name}')

'''
import mysql.connector
import csv
from io import StringIO

def run_mysql_script_and_export_to_csv(sql_file_path, csv_file_path, username, password, database, host='localhost'):
    connection_params = {
        'host': host,
        'user': username,
        'password': password,
        'database': database
    }

    connection = None
    cursor = None

    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()

        # Read SQL script from file
        with open(sql_file_path, 'r') as sql_file:
            sql_script = sql_file.read()

        # Execute the USE statement if a database is specified
        if database:
            cursor.execute(f"USE {database};")

        # Split the SQL script into individual statements
        sql_statements = sql_script.split(';')

        for statement in sql_statements:
            if statement.strip():  # Ignore empty statements
                print(f"Executing SQL: {statement.strip()}")
                cursor.execute(statement)

        # Commit changes
        connection.commit()

        # Execute the SELECT statement and capture the result in a StringIO object
        output_buffer = StringIO()
        csv_writer = csv.writer(output_buffer)

        cursor.execute("SELECT * FROM user_details;")
        rows = cursor.fetchall()

        # Write the header
        header = [i[0] for i in cursor.description]
        csv_writer.writerow(header)

        # Write the data
        csv_writer.writerows(rows)

        # Save the content to a CSV file
        with open(csv_file_path, 'w', newline='') as csv_file:
            csv_file.write(output_buffer.getvalue())

        print(f"Table exported to CSV: {csv_file_path}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

            
# Example usage
mysql_script_path = 'Sample-SQL-File-500000-Rows.sql'
csv_output_path = 'output.csv'
mysql_username = '' #username for mysql
mysql_password = '' #password for mysql
mysql_database = 'project' #database name

run_mysql_script_and_export_to_csv(mysql_script_path, csv_output_path, mysql_username, mysql_password, mysql_database)
'''

'''
#################################################################

import json
import csv

def json_to_csv(input_file, output_file):
    with open(input_file, 'r') as json_file:
        data = json_file.readlines()

        # Open CSV file for writing
        with open(output_file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)

            # Write the header based on the keys of the first JSON object
            header = json.loads(data[0]).keys()
            csv_writer.writerow(header)

            # Write each JSON object as a CSV row
            for json_str in data:
                row = json.loads(json_str)
                csv_writer.writerow(row.values())
 json_to_csv('books.json', 'outputjs.csv')

'''