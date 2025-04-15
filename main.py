from faker import Faker
import random
from models import Patient
import utils as ut

fake = Faker("pl_PL")


def generate_patients(number):
    patients = []
    for i in range(number):
        gender = random.choice(['male', 'female'])
        first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
        last_name = fake.last_name()
        date_of_birth = fake.date_of_birth(minimum_age=0, maximum_age=100)
        pesel = fake.pesel(date_of_birth, gender)
        address = fake.address().replace('\n', ', ')
        email_address = ut.generate_mail(first_name, last_name)
        phone_number = fake.phone_number()

        patient = Patient(
            id=i,
            first_name=first_name,
            last_name=last_name,
            pesel=pesel,
            gender=gender,
            date_of_birth=date_of_birth,
            address=address,
            email_address=email_address,
            phone_number=phone_number
        )
        print(patient)

        patients.append(patient)
    return patients


def write_sql_script():
    with open("script.sql", "w") as f:
        f.write("")


# write_sql_script()
generate_patients(5)
