import sys
from urllib.parse import quote_plus

from sqlalchemy import inspect, String
import random
from loaded_schema.models_generated import *

from config import *

fake = get_faker()
engine  = get_engine(sys.argv[1], quote_plus(sys.argv[2]), "test")
session = get_session(engine)

# Dictionary to track generated records for foreign key relationships
foreign_key_data = {}


def generate_table_data(table, num_records: int):
    """Generic function to generate data for a single table with support for foreign keys."""
    inspector = inspect(table)

    # Reflect columns, considering if there's a foreign key or a specific data type
    columns = inspector.columns.keys()

    data = []
    for _ in range(num_records):
        row = {}
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
                row[column_name] = fake.word()[:column.type.length]
            elif isinstance(column.type, Date):
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

    generate_table_data(Appointment, 30)  # Generate Appointments (relies on PatientCase IDs)
#

if __name__ == "__main__":
    Base.metadata.create_all(session.bind)  # Ensure tables exist
    generate_data()

