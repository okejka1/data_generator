# model_generator.py
import json
from sqlalchemy import Column, Integer, String, Date, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import importlib

Base = declarative_base()

TYPE_MAPPING = {
    "Integer": Integer,
    "String": String,
    "Date": Date,
    "DECIMAL": DECIMAL,
    "DateTime": DateTime,
    "Boolean": Boolean
}


def load_schema(schema_file):
    """Load schema from a JSON file"""
    with open(schema_file, 'r') as f:
        return json.load(f)


def create_column(column_def):
    """Create a SQLAlchemy Column from a column definition"""
    column_type = TYPE_MAPPING[column_def['type']]

    # Handle String with length
    if column_def['type'] == 'String' and 'length' in column_def:
        column_type = column_type(column_def['length'])
    # Handle DECIMAL with precision and scale
    elif column_def['type'] == 'DECIMAL' and 'precision' in column_def and 'scale' in column_def:
        column_type = column_type(column_def['precision'], column_def['scale'])

    kwargs = {
        'primary_key': column_def.get('primary_key', False),
        'nullable': column_def.get('nullable', True),
        'unique': column_def.get('unique', False)
    }

    # Handle ForeignKey
    if 'foreign_key' in column_def:
        kwargs['foreign_key'] = ForeignKey(column_def['foreign_key'])

    return Column(column_def['name'], column_type, **kwargs)


def generate_models(schema):
    """Generate SQLAlchemy models from schema"""
    models = {}
    model_relationships = {}

    # First pass: create all model classes without relationships
    for table in schema['tables']:
        attrs = {
            '__tablename__': table['name'],
        }

        # Add columns
        for column_def in table['columns']:
            attrs[column_def['name']] = create_column(column_def)

        # Keep track of relationships for second pass
        if 'relationships' in table:
            model_relationships[table['name']] = table['relationships']

        # Create the model class
        model_name = ''.join(word.capitalize() for word in table['name'].split('_'))
        models[model_name] = type(model_name, (Base,), attrs)

    # Second pass: add relationships
    for table_name, relationships in model_relationships.items():
        model_name = ''.join(word.capitalize() for word in table_name.split('_'))
        model = models[model_name]

        for rel in relationships:
            target_model = models[rel['target']]
            rel_kwargs = {
                'back_populates': rel.get('back_populates')
            }

            setattr(model, rel['name'], relationship(rel['target'], **rel_kwargs))

    # Add constants from schema
    constants = {}
    if 'constants' in schema:
        constants = schema['constants']

    return models, constants


def create_models_module(schema_file, module_name='dynamic_models'):
    """Create a Python module with the generated models"""
    schema = load_schema(schema_file)
    models, constants = generate_models(schema)

    # Create a new module
    module = importlib.util.module_from_spec(importlib.util.find_spec('builtins'))
    module.__name__ = module_name

    # Add Base to the module
    setattr(module, 'Base', Base)

    # Add models to the module
    for name, model in models.items():
        setattr(module, name, model)

    # Add constants to the module
    for name, value in constants.items():
        setattr(module, name, value)

    # Create a list of table names
    table_names = {table['name'] for table in schema['tables']}
    setattr(module, 'LIST_OF_TABLES', table_names)

    return module