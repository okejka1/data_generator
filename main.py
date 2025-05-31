import sys
from typing import List
from faker import Faker
import random

import models
import utils
from models import *
import utils as ut
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, time
import pymysql

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
def delete_data_from_tables():
    session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    for table in LIST_OF_TABLES:
        session.execute(text(f"DELETE FROM {table};"))
        session.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1;"))
    session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    session.commit()

# Work hours in each department are 8-18 every day
# Consider adding a new table employee
def generate_department_responsiblity(range_days) -> List[DepartmentResponsibility]:
    department_responsibilities = []
    department_list = DEPARTMENTS

    now = datetime.now()

    start_date = now - (timedelta(days=range_days)/2)
    work_start_time = time(8, 0)  # 8:00
    work_end_time = time(18, 0)  # 18:00

    for dept_name in department_list:
        current_date = start_date

        for _ in range(range_days):
            time_from = datetime.combine(current_date.date(), work_start_time)
            time_to = datetime.combine(current_date.date(), work_end_time)

            # TODO: Consider limiting employee (e.g. csv with names and roles)
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
            end = start + timedelta(days=duration_days) if random.random() > 0.7 else None

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


def generate_appointment_statuses() -> List[AppointmentStatus]:
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

'''
STEPS TO GENERATE APPOINTMENTS:
1. Get the list of all patients' ids from a patient_cases list in order to do not crate overlapping appointments.
2. Get the list of all the department responsibilities (known days with doctors' shifts in each department).
3. Get patient_cases for now only active ones (means these which does not have end_time). From patient_cases w
4. For each department and each patient case create appointments for each day in the range of 8:00 - 18:00.
5. For each appointment, determine the status based on the current time.

'''
def generate_appointments(patient_cases, department_responsibilities, appointment_statuses, number_of_appointments):
    appointments = []

    appointments_by_patient = {case.patient.id: [] for case in patient_cases }  # Track appointments for each patient

    # Prepare a list of valid department responsibilities
    valid_responsibilities = [resp for resp in department_responsibilities]

    # Generate time slots between 8:00 AM and 6:00 PM (10 total slots, hourly)
    time_slots = [datetime.combine(datetime.today(), time(8, 0)) + timedelta(hours=i) for i in range(10)]

    # Generate the desired number of appointments
    for _ in range(number_of_appointments):
        # Randomly pick a department responsibility (random department and day)
        dept_resp = random.choice(valid_responsibilities)
        date = dept_resp.time_from.date()

        # List available cases
        available_cases = [
            case for case in patient_cases
            if case.in_progress and case.start_time.date() <= date and case.end_time is None
        ]
        if not available_cases:
            continue  # Skip if no valid cases are available

        case = random.choice(available_cases)
        patient_id = case.patient.id

        # Randomly choose a time slot
        random_slot = random.choice(time_slots)
        appointment_start = random_slot
        duration = timedelta(minutes=random.randint(30, 55))
        appointment_end = appointment_start + duration

        # Ensure no overlapping appointments for this patient
        if any(
            appointment_start < end and appointment_end > start  # Overlapping condition
            for start, end in appointments_by_patient[patient_id]
        ):
            continue  # Skip if time slot is already occupied

        # Determine appointment status based on current time
        current_time = datetime.now()
        if appointment_start > current_time:
            status = next(s for s in appointment_statuses if s.status_name == "To do")
        elif appointment_end > current_time:
            status = next(s for s in appointment_statuses if s.status_name == "In progress")
        else:
            status = next(s for s in appointment_statuses if s.status_name == "Done")

        # Set creation time for the appointment
        time_created = min(
            appointment_start - timedelta(days=random.randint(1, 7)), case.start_time
        )

        # Create the appointment
        appointment = Appointment(
            patient_caseid=case.id,
            in_departmentid=dept_resp.id,
            time_created=time_created,
            appointment_start_time=appointment_start,
            appointment_end_time=appointment_end,
            appointment_statusid=status.id,
        )

        # Save the appointment
        session.add(appointment)
        appointments.append(appointment)
        appointments_by_patient[patient_id].append((appointment_start, appointment_end))  # Track this patient's appointments

    # Commit the appointments to the database
    session.commit()

    # Output
    for appointment in appointments:
        print(f"Appointment ID: {appointment.id}, "
              f"Case ID: {appointment.patient_caseid}, "
              f"Department: {appointment.department_responsibility.department_name}, "
              f"Date: {appointment.appointment_start_time.date()}, "
              f"Time: {appointment.appointment_start_time.time()} - {appointment.appointment_end_time.time()}")

    return appointments

def generate_appointment_histories(appointments):
    appointment_histories = []

    for appointment in appointments:
        time_created = appointment.time_created

        status_id = appointment.appointment_statusid

        # TO DO status:
        if status_id == 1:
            history = AppointmentHistory(
                appointmentid=appointment.id,
                appointment_statusid=1,
                status_time=time_created
            )
            appointment_histories.append(history)

        # In progress status:
        elif status_id == 2:
            history_to_do = AppointmentHistory(
                appointmentid=appointment.id,
                appointment_statusid=1,  # "To do"
                status_time=time_created
            )
            history_in_progress = AppointmentHistory(
                appointmentid=appointment.id,
                appointment_statusid=2,  # "In progress"
                status_time=appointment.appointment_start_time
            )
            appointment_histories.extend([history_to_do, history_in_progress])

        # Done status:
        elif status_id == 3:
            history_to_do = AppointmentHistory(
                appointmentid=appointment.id,
                appointment_statusid=1,  # "To do"
                status_time=time_created
            )
            history_in_progress = AppointmentHistory(
                appointmentid=appointment.id,
                appointment_statusid=2,  # "In progress"
                status_time=appointment.appointment_start_time
            )
            history_done = AppointmentHistory(
                appointmentid=appointment.id,
                appointment_statusid=3,  # "Done"
                status_time=appointment.appointment_end_time
            )
            appointment_histories.extend([history_to_do, history_in_progress, history_done])

    session.add_all(appointment_histories)
    session.commit()

    for history in appointment_histories:
        print(f"Created History: Appointment ID {history.appointmentid}, Status ID {history.appointment_statusid}, Time {history.status_time}")

    return appointment_histories

def generate_documents(appointments):
    docs = []
    for appointment in appointments:
        docs.append(generate_document_by_appointment(appointment))
    session.add_all(docs)
    session.commit()
    return docs

# def generate_documents_by_patient_case(patient_cases, document_type, num_documents_per_case=1):
#     documents = []
#     for case in patient_cases:
#         for _ in range(num_documents_per_case):
#
#     for doc in documents:
#         print(f"Document Internal Number: {doc.document_internal_number}, "
#               f"Name: {doc.document_name}, Type: {doc.document_type.type_name}, URL: {doc.document_url}")
#
#     return documents

def generate_document_by_appointment(appointment):
    # Dynamically fetch valid IDs for document_type from the database
    document_type_ids = [doc_type.id for doc_type in session.query(DocumentType).all()]
    
    if not document_type_ids:
        raise ValueError("No document types found in the database!")

    # Pick a random ID from the valid document type IDs
    doc_type_id = random.choice(document_type_ids)

    # Optionally generate a description
    description = fake.paragraph(nb_sentences=2) if random.random() > 0.5 else ""

    # Generate the document
    doc = Document(
        appointmentid=appointment.id,
        document_typeid=doc_type_id,  # Use valid database ID
        document_internal=str(uuid.uuid4()),  # Unique UUID
        document_name=utils.generate_document_name(session.query(DocumentType).get(doc_type_id).type_name),
        document_url=f"https://www.example.com/documents/{uuid.uuid4()}.pdf",
        time_created=datetime.now(),
        details=description
    )
    session.add(doc)
    session.commit()
    return doc


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

print("LOG | Deleting data")
delete_data_from_tables()
print("LOG | Generating patients")
patients = generate_patients(100)
print("LOG | Generating patient cases")
patient_cases = generate_patient_cases(patients)
print("LOG | Generating department responsibilities")
department_responsibilities = generate_department_responsiblity(60)
print("LOG | Generating appointment statuses")
statuses = generate_appointment_statuses()
print("LOG | Generating document types")
generate_document_types()
print("LOG | Generating appointments")
appointments = generate_appointments(patient_cases, department_responsibilities, statuses, 200)
print("LOG | Generating appointment histories")
generate_appointment_histories(appointments)
print("LOG | Generating documents")
generate_documents(appointments)
print("LOG | Closing session")
session.close()