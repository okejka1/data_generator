import random
import string

def generate_mail(name: str, last_name: str):
    return f'{name.lower()}.{last_name.lower()}@poczta.pl'

def generate_document_name(document_type: str):
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    return f'{document_type.lower()}_{random_str}.pdf'