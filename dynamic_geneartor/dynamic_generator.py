import sys
from urllib.parse import quote_plus

from sqlalchemy import inspect, String
import random
from loaded_schema.models_generated import Base, Patient, PatientCase

from config import *

fake = get_faker()
engine  = get_engine(sys.argv[1], quote_plus(sys.argv[2]), "clinic_database")
session = get_session(engine)

def generate_table_data(table, num_records: int):
    """Generic function to generate data for a single table."""
    inspector = inspect(table)
    columns = inspector.columns.keys()
    data = []

    for _ in range(num_records):
        row = {}
        for column_name in columns:
            column_type = inspector.columns[column_name].type
            if column_name == "id":  # Handle primary key as auto-increment
                continue
            elif isinstance(column_type, (Integer, Boolean)):
                row[column_name] = random.randint(1, 100)
            elif isinstance(column_type, String):
                row[column_name] = fake.word()[:column_type.length]
            elif isinstance(column_type, DateTime):
                row[column_name] = fake.date_time()
            elif isinstance(column_type, Date):
                row[column_name] = fake.date_of_birth()
            elif isinstance(column_type, DECIMAL):
                row[column_name] = round(random.uniform(10.0, 1000.0), 2)
            else:
                row[column_name] = None
        data.append(row)

    session.add_all([table(**entry) for entry in data])
    print(f"{len(data)} records inserted into {table.__tablename__}")
    return data


# Example: Generate data for Patient dynamically
generate_table_data(Patient, 10)
generate_table_data(PatientCase, 10)
