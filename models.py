from sqlalchemy import Column, Integer, String, Date, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


'''
MVP of data generator:
create data generator which generates data for the following tables:
- department_responsibility - DONE
- patient - DONE
- patient_case - DONE
- appointment
- appointment_status - DONE
- appointment_history
- document_type - DONE
- document

and output is sql script which can be executed on mysql database.
Requirement for MVP is for database to be cleared before running data generator.

Further steps would include adding records on already filled tables.

'''


LIST_OF_TABLES = {"department_responsibility", "patient", "patient_case", "appointment", "appointment_status", "status_history", "document_type", "document"}
Base = declarative_base()

DEPARTMENTS = [
    "Kardiologia", "Neurologia", "Pediatria", "Ortopedia",
    "Dermatologia", "Chirurgia", "Ginekologia", "Urologia", "Endokrynologia",
    "Onkologia"
]

APPOINTMENT_STATUSES = ["zaplanowany", "w trakcie", "zakocznony"]

DOCUMENT_TYPES = [
    "Karta pacjenta",
    "Wynik badania",
    "Recepta",
    "Skierowanie",
    "Historia choroby",
    "Zalecenia lekarskie",
    "Zaświadczenie lekarskie",
    "Zgoda na zabieg",
    "Karta szczepień",
    "Dokumentacja obrazowa"
]


class DepartmentResponsibility(Base):
    __tablename__ = 'department_responsibility'

    id = Column(Integer, primary_key=True)
    employee_full_name = Column(String(255))
    department_name = Column(String(255))
    time_from = Column(DateTime)
    time_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean)

    appointments = relationship("Appointment", back_populates="department_responsibility")
    documents = relationship("Document", back_populates="department_responsibility")

    def __str__(self):
        return (f'{self.id}, {self.employee_full_name} {self.department_name}, {self.time_from}, {self.time_to}, {self.is_active}')

class Patient(Base):
    __tablename__ = 'patient'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(64))
    last_name = Column(String(64))
    pesel = Column(String(11), unique=True)
    gender = Column(String(64))
    date_of_birth = Column(Date)
    address = Column(String(255))
    email_address = Column(String(64), nullable=True)
    phone_number = Column(String(20), nullable=True)

    patient_cases = relationship("PatientCase", back_populates="patient")
    documents = relationship("Document", back_populates="patient")

    def __str__(self):
        return (f'{self.id}, {self.first_name} {self.last_name}, {self.pesel}, {self.date_of_birth}, {self.address},'
                f' {self.email_address}, {self.phone_number}')

    def to_sql(self):
        return 'INSERT'

class PatientCase(Base):
    __tablename__ = 'patient_case'

    id = Column(Integer, primary_key=True)
    patientid = Column(Integer, ForeignKey("patient.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    in_progress = Column(Boolean)
    total_cost = Column(DECIMAL(10, 2), nullable=True)
    amount_paid = Column(DECIMAL(10, 2), nullable=True)

    patient = relationship("Patient", back_populates="patient_cases")
    documents = relationship("Document", back_populates="patient_case")
    appointments = relationship("Appointment", back_populates="patient_case")

    def __str__(self):
        return (f'patientid={self.patient.id} {self.start_time}, {self.end_time}, {self.in_progress}, {self.total_cost},'
                f' {self.amount_paid}')


class Appointment(Base):
    __tablename__ = 'appointment'

    id = Column(Integer, primary_key=True)
    patient_case_id = Column(Integer, ForeignKey("patient_case.id"))
    department_responsibility_id = Column(Integer, ForeignKey("department_responsibility.id"))
    time_created = Column(DateTime)
    appointment_start_time = Column(DateTime)
    appointment_end_time = Column(DateTime, nullable=True)
    appointment_status_id = Column(Integer, ForeignKey("appointment_status.id"))

    patient_case = relationship("PatientCase", back_populates="appointments")
    department_responsibility = relationship("DepartmentResponsibility", back_populates="appointments")
    appointment_status = relationship("AppointmentStatus", back_populates="appointments")
    documents = relationship("Document", back_populates="appointment")
    appointment_histories = relationship("AppointmentHistory", back_populates="appointment")


class AppointmentStatus(Base):
    __tablename__ = 'appointment_status'

    id = Column(Integer, primary_key=True)
    status_name = Column(String(64), unique=True)

    appointments = relationship("Appointment", back_populates="appointment_status")
    appointment_histories = relationship("AppointmentHistory", back_populates="appointment_status")

    def __str__(self):
        return (f'{self.id}, {self.status_name}')


class AppointmentHistory(Base):
    __tablename__ = 'status_history'

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"))
    appointment_status_id = Column(Integer, ForeignKey("appointment_status.id"))
    status_time = Column(DateTime)

    appointment = relationship("Appointment", back_populates="appointment_histories")
    appointment_status = relationship("AppointmentStatus", back_populates="appointment_histories")


class DocumentType(Base):
    __tablename__ = 'document_type'

    id = Column(Integer, primary_key=True)
    type_name = Column(String(64), unique=True)

    documents = relationship("Document", back_populates="document_type")


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True)
    document_internal_number = Column(Integer, unique=True)
    document_name = Column(String(255))
    time_created = Column(DateTime)
    document_url = Column(String(255))
    details = Column(String(1000), nullable=True)

    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=True)
    patient_case_id = Column(Integer, ForeignKey("patient_case.id"), nullable=True)
    department_responsibility_id = Column(Integer, ForeignKey("department_responsibility.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=True)
    document_type_id = Column(Integer, ForeignKey("document_type.id"), nullable=True)

    patient = relationship("Patient", back_populates="documents")
    patient_case = relationship("PatientCase", back_populates="documents")
    department_responsibility = relationship("DepartmentResponsibility", back_populates="documents")
    appointment = relationship("Appointment", back_populates="documents")
    document_type = relationship("DocumentType", back_populates="documents")