import json

def render_column(col):
    if col['type'] == "DECIMAL":
        precision = col.get("precision", 10)
        scale = col.get("scale", 2)
        line = f"{col['name']} = Column(DECIMAL({precision}, {scale})"
    else:
        line = f"{col['name']} = Column({col['type']}"
    if col.get('length'):
        line += f"({col['length']})"
    if col.get('primary_key'):
        line += ", primary_key=True"
    if col.get('unique'):
        line += ", unique=True"
    if col.get('foreign_key'):
        line += f", ForeignKey('{col['foreign_key']}')"
    if col.get('nullable') is not None:
        line += f", nullable={col['nullable']}"
    line += ")"
    return line


def generate_python_code(schema):
    s = [
        "from sqlalchemy.ext.declarative import declarative_base",
        "from sqlalchemy import Column, Integer, String, Date, DECIMAL, DateTime, Boolean, ForeignKey",
        "from sqlalchemy.orm import relationship",
        "",
        "Base = declarative_base()",
        "",
    ]
    for table in schema['tables']:
        class_name = ''.join([w.capitalize() for w in table['name'].split('_')])
        s.append(f"class {class_name}(Base):")
        s.append(f"    __tablename__ = '{table['name']}'")
        for col in table['columns']:
            s.append(f"    {render_column(col)}")

        if 'relationships' in table:
            for rel in table['relationships']:
                target_class = ''.join([word.capitalize() for word in rel['target'].split('_')])
                back_populates = rel['back_populates']
                rel_name = rel['name']
                s.append(f"    {rel_name} = relationship('{target_class}', back_populates='{back_populates}')")
        s.append("")
    return '\n'.join(s)

with open('input/full_schema.json') as f:
    schema = json.load(f)

code = generate_python_code(schema)
with open('loaded_schema/models_generated.py', 'w') as f:
    f.write(code)
