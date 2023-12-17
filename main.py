import psycopg2
import pandas as pd
import numpy as np
from tqdm import tqdm
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
def import_csv_to_postgres(csv_file, table_name, db_credentials):
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**db_credentials)
        cursor = connection.cursor()
        drop = "DROP TABLE IF EXISTS " + table_name
        
        # Get the column names and datatypes from the DataFrame
        column_names = list(csv_file.columns)
        datatypes = [map_data_type(csv_file[col].dtype) for col in column_names]
        
        # Generate the create_table_query
        create_table_query = f"""
        CREATE TABLE {table_name} (
            {", ".join([f'"{col}" {dtype}' for col, dtype in zip(column_names, datatypes)])}
        );
        """
        
        # Create the table in the database if it doesn't exist
        cursor.execute(drop)
        cursor.execute(create_table_query)
        connection.commit()

        # Convert the DataFrame to a list of tuples
        data = [tuple(convert_value(value) for value in row) for row in csv_file.to_records(index=False)]

        # Prepare the query for bulk insertion
        insert_query = f"INSERT INTO {table_name} VALUES ({', '.join(['%s'] * len(column_names))})"
        
        # Add loading screen using tqdm
        with tqdm(total=len(data), desc="Importing data") as pbar:
            # Execute the bulk insertion
            for chunk in chunks(data, 1000):  # Insert data in chunks of 1000 rows
                cursor.executemany(insert_query, chunk)
                connection.commit()
                pbar.update(len(chunk))

        print("Data imported successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while importing data to PostgreSQL:", error)

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def map_data_type(dtype):
    if dtype == 'int64' or dtype == 'int32':
        return 'smallint'
    elif dtype == 'float64':
        return 'decimal'
    elif dtype == 'bool':
        return 'boolean'
    elif dtype == 'object':
        return 'text'
    # Add more data type mappings as needed
    else:
        return 'text'  # Default to text data type if no match is found

def convert_value(value):
    if isinstance(value, np.int64):
        return int(value)
    else:
        return value

# Set the CSV file path, table name, and database credentials
db_credentials = {
    "user": "USER_NAME",
    "password": "PASS_",
    "host": "HOST_NAME",
    "port": "5432",
    "database": "YOUR_DB_NAME"
}

# Read the CSV files into DataFrames
Path = pd.read_csv("PATH") 

# Call the function to import the DataFrame data to PostgreSQL
import_csv_to_postgres(Path, 'Training_data', db_credentials)
