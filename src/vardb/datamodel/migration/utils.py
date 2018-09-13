from contextlib import contextmanager

import sqlalchemy as sa


@contextmanager
def update_enum(op, table_names, column, enum_name, old_options, new_options, nullable=False):

    if not isinstance(table_names, list):
        table_names = [table_names]

    ALTER_TABLE_TEMPLATE = 'ALTER TABLE {table_name} ALTER COLUMN {column} TYPE {enum_type} USING {column}::text::{enum_type}'

    all_options = list(set(old_options + new_options))
    tmp_type_name = '__' + enum_name
    old_type = sa.Enum(*old_options, name=enum_name)
    new_type = sa.Enum(*new_options, name=enum_name)
    tmp_type = sa.Enum(*all_options, name=tmp_type_name)

    # Create a tempoary type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)

    sq_tables = list()
    for table_name in table_names:
        sq_table = sa.sql.table(table_name, sa.Column(column, new_type, nullable=nullable))

        op.execute(ALTER_TABLE_TEMPLATE.format(
            table_name=table_name,
            column=column,
            enum_type=tmp_type_name
        ))
        sq_tables.append(sq_table)

    old_type.drop(op.get_bind(), checkfirst=False)
    # Yield table with the tmp combined enum so caller can migrate the values
    yield sq_tables if len(sq_tables) > 1 else sq_tables[0]

    # Alter table to use new enum
    new_type.create(op.get_bind(), checkfirst=False)
    for table_name in table_names:
        op.execute(ALTER_TABLE_TEMPLATE.format(
            table_name=table_name,
            column=column,
            enum_type=enum_name
        ))
    tmp_type.drop(op.get_bind(), checkfirst=False)
