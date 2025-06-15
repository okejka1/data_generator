import json
import sys
from urllib.parse import quote_plus

from sqlalchemy import inspect, String
import random
from loaded_schema.models_generated import *

from config import *
from static_generator.models import AppointmentHistory

fake = get_faker()
engine  = get_engine(sys.argv[1], quote_plus(sys.argv[2]), "test")
session = get_session(engine)

# Dictionary to track generated records for foreign key relationships
foreign_key_data = {}

schema_path = 'input/full_schema.json'
with open(schema_path) as f:
    full_schema = json.load(f)
constants = full_schema.get("constants", {})

def choose_constant(table, column_name):
    for col in full_schema['tables']:
        if col['name'] == table.__tablename__:
            for c in col.get('columns', []):
                if c['name'] == column_name and 'constants_ref' in c:
                    return constants.get(c['constants_ref'], [])
    return None


def generate_table_data(table, num_records: int):
    """Generic function to generate data for a single table with support for foreign keys."""
    inspector = inspect(table)

    # Reflect columns, considering if there's a foreign key or a specific data type
    columns = inspector.columns.keys()

    data = []
    for _ in range(num_records):
        row = {}
        date_birth = fake.date_of_birth()
        gender = random.choice(['male', 'female'])
        pesel = fake.pesel(date_birth, gender)

        for column_name in columns:
            column = inspector.columns[column_name]

            if column.primary_key:  # Skip primary keys (assume auto-increment)
                continue

            if column.foreign_keys:  # Handle foreign keys
                fk = list(column.foreign_keys)[0]  # Get foreign key reference
                referenced_table_name = fk.column.table.name

                # Lookup existing foreign key data
                if referenced_table_name in foreign_key_data and foreign_key_data[referenced_table_name]:
                    row[column_name] = random.choice(foreign_key_data[referenced_table_name])
                else:
                    # If referenced data is empty, raise an error
                    raise ValueError(
                        f"No records found for foreign key table `{referenced_table_name}`. Please generate data for it first.")

            elif isinstance(column.type, Integer):
                row[column_name] = random.randint(1, 100)
            elif isinstance(column.type, String):
                const_choices = choose_constant(table, column_name)
                if const_choices:
                    row[column_name] = random.choice(const_choices)
                elif(column_name == "first_name"):
                    row[column_name] = fake.first_name_male() if gender == 'male' else fake.first_name_female()
                elif(column_name == "last_name"):
                    row[column_name] = fake.last_name()
                elif(column_name == "email_address"):
                    row[column_name] = fake.email()
                elif(column_name == "phone_number"):
                    row[column_name] = fake.phone_number()
                elif(column_name == "address"):
                    row[column_name] = fake.address().replace('\n', ', ')
                elif(column_name == "pesel"):
                    row[column_name] = pesel
                elif(column_name == "gender"):
                    row[column_name] = gender
                else:
                    row[column_name] = fake.word()[:column.type.length]
            elif isinstance(column.type, Date):
                if(column_name == "date_of_birth"):
                    row[column_name] = date_birth
                else:
                    row[column_name] = fake.date_of_birth()
            elif isinstance(column.type, DateTime):
                row[column_name] = fake.date_time()
            elif isinstance(column.type, DECIMAL):
                row[column_name] = round(random.uniform(10.0, 1000.0), 2)
            elif isinstance(column.type, Boolean):
                row[column_name] = random.choice([True, False])
            else:
                row[column_name] = None
        data.append(row)

    # Save generated records into the database
    session.add_all([table(**entry) for entry in data])
    session.commit()

    # Store the generated primary keys for foreign key relationship handling
    if hasattr(table, '__tablename__'):
        stored_primary_keys = [getattr(item, 'id') for item in session.query(table).all()]
        foreign_key_data[table.__tablename__] = stored_primary_keys

    print(f"{len(data)} records inserted into `{table.__tablename__}`.")
    return data


# Example: Generate data for all tables while handling relationships
def generate_data():

    # Generate tables in the correct dependency order
    # Note: Order matters due to foreign key dependencies!
    generate_table_data(Patient, 10)  # Generate Patients first (no dependencies)
    generate_table_data(DepartmentResponsibility, 10)
    generate_table_data(PatientCase, 20)  # Generate Patient Cases (relies on Patient IDs)
    generate_table_data(AppointmentStatus, 3)
    generate_table_data(DocumentType, 3)

    generate_table_data(Appointment, 30)  # Generate Appointments (relies on PatientCase IDs)
    generate_table_data(AppointmentHistory, 30)
    generate_table_data(Document, 30)
#

if __name__ == "__main__":
    Base.metadata.drop_all(session.bind)
    Base.metadata.create_all(session.bind)  # Ensure tables exist
    generate_data()


