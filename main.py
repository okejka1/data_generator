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


def generate_appointments(patient_cases, department_responsibilities, appointment_statuses):
    appointments = []

    # Group department responsibilities by department and date
    dept_schedule = {}
    for dept_resp in department_responsibilities:
        date_key = dept_resp.time_from.date()
        dept_key = dept_resp.department_name
        if (dept_key, date_key) not in dept_schedule:
            dept_schedule[(dept_key, date_key)] = []
        dept_schedule[(dept_key, date_key)].append(dept_resp)

    # For each department and day, create appointments
    for (dept_name, date), dept_resps in dept_schedule.items():
        if not dept_resps:
            continue

        dept_resp = dept_resps[0]

        # Create fixed time slots from 8:00 to 18:00
        time_slots = []
        slot_duration = timedelta(minutes=60)

        current_time = datetime.combine(date, time(8, 0))
        end_time = datetime.combine(date, time(18, 0))

        while current_time + slot_duration <= end_time:
            time_slots.append(current_time)
            current_time += slot_duration

        # Get only active (not ended) cases for this day
        available_cases = [
            case for case in patient_cases
            if case.start_time.date() <= date
               and case.end_time is None  # Case must be active (not ended)
               and case.in_progress  # Must be in progress
        ]

        if not available_cases:
            continue

        # Create appointments for each time slot
        for slot_time in time_slots:
            if not available_cases:
                # Refresh available cases if we run out
                available_cases = [
                    case for case in patient_cases
                    if case.start_time.date() <= date
                       and case.end_time is None
                       and case.in_progress
                ]
                if not available_cases:
                    break

            case = random.choice(available_cases)
            available_cases.remove(case)

            duration = timedelta(minutes=random.randint(30, 55))
            appointment_start = slot_time
            appointment_end = slot_time + duration

            # Determine status based on current time
            current_time = datetime.now()
            if appointment_start > current_time:
                status = next(s for s in appointment_statuses if s.status_name.lower() == "zaplanowany")
            elif appointment_end > current_time:
                status = next(s for s in appointment_statuses if s.status_name.lower() == "w trakcie")
            else:
                status = next(s for s in appointment_statuses if s.status_name.lower() == "zakończony")

            time_created = min(
                appointment_start - timedelta(days=random.randint(1, 7)),
                case.start_time
            )

            appointment = Appointment(
                patient_case_id=case.id,
                department_responsibility_id=dept_resp.id,
                time_created=time_created,
                appointment_start_time=appointment_start,
                appointment_end_time=appointment_end,
                appointment_status_id=status.id
            )

            session.add(appointment)
            appointments.append(appointment)

    session.commit()

    for appointment in appointments:
        print(f"Appointment ID: {appointment.id}, "
              f"Case ID: {appointment.patient_case_id}, "
              f"Department: {appointment.department_responsibility.department_name}, "
              f"Date: {appointment.appointment_start_time.date()}, "
              f"Time: {appointment.appointment_start_time.time()} - {appointment.appointment_end_time.time()}")

    return appointments

#
# def generate_appointment_history(appointments, appointment_statuses):
#     histories = []
#
#     for appointment in appointments:
#         planned_status = next(s for s in appointment_statuses if s.status_name == "zaplanowany")
#         in_progress_status = next(s for s in appointment_statuses if s.status_name == "w trakcie")
#         completed_status = next(s for s in appointment_statuses if s.status_name == "zakocznony")
#
#         history = AppointmentHistory(
#             appointment_id=appointment.id,
#             appointment_status_id=planned_status.id,
#             status_time=appointment.time_created
#         )
#         session.add(history)
#         histories.append(history)
#
#         current_time = datetime.now()
#
#         # Add "in progress" status if appointment has started
#         if current_time >= appointment.appointment_start_time:
#             history = AppointmentHistory(
#                 appointment_id=appointment.id,
#                 appointment_status_id=in_progress_status.id,
#                 status_time=appointment.appointment_start_time
#             )
#             session.add(history)
#             histories.append(history)
#
#             # Add "completed" status if appointment has ended
#             if appointment.appointment_end_time and current_time >= appointment.appointment_end_time:
#                 history = AppointmentHistory(
#                     appointment_id=appointment.id,
#                     appointment_status_id=completed_status.id,
#                     status_time=appointment.appointment_end_time
#                 )
#                 session.add(history)
#                 histories.append(history)
#
#     session.commit()
#     for history in histories:
#         print(f"History - Appointment ID: {history.appointment_id}, "
#               f"Status ID: {history.appointment_status_id}, Time: {history.status_time}")
#     return histories


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