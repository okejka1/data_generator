from faker import Faker

from models import Patient


# word = "python"
#
# # print(word[2:4])
# print(word[4: ])
# print(word[-2: ])
# # print(word[4:0])
# # print(word[:-2])
# # print(word[:2])
#
# # Python strings cannot be changed — they are immutable.
# # Therefore, assigning to an indexed position in the string results in an error:
# new_word = word[:] + 'w'
# print(new_word)
# s = "qweq"
# print(len(s))
#
# squares = [1,4,9,16,25]
# squares.append(22)
# squares[:] = []
# print(squares)
#
#
# a,b = 0,1
# while a < 10:
#     print(a)
#     a, b=b, a+b
#
#
def generate_patients(number):
    patients = []
    for i in number:
        patients.append(Patient(

        ))


def write_sql_script():
    with open("script.sql", "w") as f:
        f.write("")

write_sql_script()