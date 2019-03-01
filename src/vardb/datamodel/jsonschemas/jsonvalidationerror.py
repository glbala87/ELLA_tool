import jsonschema
from vardb.datamodel import jsonschema as dbjsonschema


class JSONValidationError(Exception):
    pass


def concatenate_json_validation_errors(session, data, schema_name):

    available_schemas = (
        session.query(dbjsonschema.JSONSchema.version, dbjsonschema.JSONSchema.schema)
        .filter(dbjsonschema.JSONSchema.name == schema_name)
        .order_by(dbjsonschema.JSONSchema.version.desc())
        .all()
    )

    error_message = []
    for version, schema in available_schemas:
        error_message.append(
            "\n*** Schema ({}, {}) failed with the exception:".format(schema_name, version)
        )
        try:
            jsonschema.validate(data, schema)
            error_message.append(
                "Unexpectedly passed python jsonschema validate. This suggests a discrepancy between postgres json validation and python json validation.".format(
                    schema_name, version
                )
            )
        except jsonschema.ValidationError as e:
            error_message.append(format(e))

    return "\n".join(error_message)
