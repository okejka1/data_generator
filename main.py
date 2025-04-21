import sys
from typing import List
from faker import Faker
import random
from models import *
import utils as ut
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, time
from models import DEPARTMENTS
from models import LIST_OF_TABLES

# TODO: IMPROVE READABILITY OF THE CODE
# TODO: ADJUST DELETION OF DATA RECORDS TO NOT THROW ERRORS ON DB CLEARANCE

if len(sys.argv) < 3:
    print("provide DB credentials")
    sys.exit()

fake = Faker("pl_PL")
from urllib.parse import quote_plus
import sys

username = sys.argv[1]
password = quote_plus(sys.argv[2])  # Properly escape special chars like '@'

engine = create_engine(f'mysql+pymysql://{username}:{password}@127.0.0.1:3306/clinic_database', echo=True)

# engine = create_engine(f'mysql+pymysql://{sys.argv[1]}:@localhost:3306/clinic_database', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)
for table in LIST_OF_TABLES:
    session.execute(text(f"DELETE FROM {table};"))
session.commit()

# Work hours in each department are 8-18 everyday
# Consider adding new table employee
def generate_department_responsiblity(range_days) -> List[DepartmentResponsibility]:
    department_responsibilities = []
    department_list = DEPARTMENTS

    now = datetime.now()

    start_date = now - (timedelta(days=range_days)/2)
    work_start_time = time(8, 0)  # 8:00
    work_end_time = time(18, 0)  # 18:00

    for i in range(len(department_list)):
        dept_name = department_list[i % len(department_list)]
        current_date = start_date

        for _ in range(range_days):
            time_from = datetime.combine(current_date.date(), work_start_time)
            time_to = datetime.combine(current_date.date(), work_end_time)

            gender = random.choice(['male', 'female'])
            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            last_name = fake.last_name()
            employee_full_name = f"{first_name} {last_name}"
            is_active = (now >= time_from and now <= time_to and
                         now.date() == current_date.date())

            dept_responsibility = DepartmentResponsibility(
                employee_full_name=employee_full_name,
                department_name=dept_name,
                time_from=time_from,
                time_to=time_to,
                is_active=is_active
            )
            session.add(dept_responsibility)
            department_responsibilities.append(dept_responsibility)

            current_date += timedelta(days=1)
    session.commit()
    for de in department_responsibilities:
        print(de)
    return department_responsibilities


def generate_patients(number):
    patients = []
    for _ in range(number):
        gender = random.choice(['male', 'female'])
        first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
        last_name = fake.last_name()
        date_of_birth = fake.date_of_birth(minimum_age=0, maximum_age=100)
        pesel = fake.pesel(date_of_birth, gender)
        address = fake.address().replace('\n', ', ')
        email_address = ut.generate_mail(first_name, last_name)
        phone_number = fake.phone_number()

        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            pesel=pesel,
            gender=gender,
            date_of_birth=date_of_birth,
            address=address,
            email_address=email_address,
            phone_number=phone_number
        )

        session.add(patient)
        patients.append(patient)
    session.commit()
    for patient in patients:
        print(patient)
    return patients


def generate_patient_cases(patients, cases_per_patient=1):
    patient_cases = []

    for i, patient in enumerate(patients):
        for _ in range(cases_per_patient):
            start = fake.date_time_between(start_date='-2y', end_date='now')
            duration_days = random.randint(1, 30)
            end = start + timedelta(days=duration_days) if random.random() > 0.3 else None

            total_cost = round(random.uniform(100, 10000), 2)
            amount_paid = round(total_cost * random.uniform(0.5, 1.0), 2)

            case = PatientCase(
                patient=patient,
                start_time=start,
                end_time=end,
                in_progress=end is None,
                total_cost=total_cost,
                amount_paid=amount_paid
            )
            print(case)
            session.add(case)
            patient_cases.append(case)
    session.commit()
    return patient_cases

def generate_appointment_statuses() ->List[AppointmentStatus]:
    statuses = []
    for status in APPOINTMENT_STATUSES:
        status = AppointmentStatus(
            status_name=status,
        )
        print(status)
        session.add(status)
        statuses.append(status)
    session.commit()
    return statuses

def generate_document_types() -> List[DocumentType]:
    document_types = []
    for _type_name in DOCUMENT_TYPES:
        document_type = DocumentType(
            type_name=_type_name
        )
        print(document_type)
        session.add(document_type)
        document_types.append(document_type)
    session.commit()
    return document_types


def write_sql_script(table_name, patients):
    with open("script.sql", "w") as f:
        # First, write the statement to reset auto_increment
        f.write(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;\n")


        for i, patient in enumerate(patients, start=1):
            date_str = patient.date_of_birth.strftime('%Y-%m-%d')
            sql = f"""INSERT INTO {table_name} 
                    (id, first_name, last_name, pesel, gender, date_of_birth, address, email_address, phone_number) 
                    VALUES 
                    ({i}, '{patient.first_name}', '{patient.last_name}', '{patient.pesel}', 
                    '{patient.gender}', '{date_str}', '{patient.address}', 
                    '{patient.email_address}', '{patient.phone_number}');\n"""
            f.write(sql)
    f.close()

patients = generate_patients(5)
generate_patient_cases(patients)
generate_department_responsiblity(30)
generate_appointment_statuses()
generate_document_types()

session.close()