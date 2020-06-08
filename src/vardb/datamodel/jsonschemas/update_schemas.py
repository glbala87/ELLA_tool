import os
import json
import re
import jsonschema
from vardb.util.db import DB
from vardb.datamodel.jsonschema import JSONSchema
from .load_schema import load_schema


def update_schemas(session):
    create_jsonschema_sql_functions(session)
    create_schema_triggers(session)
    base_path = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(base_path):
        m = re.match("(?P<name>[a-z]+)_v(?P<version>[0-9]+).json$", filename)
        if not m:
            continue

        name = m.groupdict()["name"]
        version = m.groupdict()["version"]
        schema = load_schema(filename)

        # Check that schema is valid
        jsonschema.Draft4Validator.check_schema(schema)

        # Load all refs (jsonref lazy loads references, and can only be circumvented with the "load_on_repr" flag)
        schema = json.loads(
            repr(schema).replace("'", '"').replace("False", "false").replace("True", "true")
        )

        existing = (
            session.query(JSONSchema)
            .filter(JSONSchema.name == name, JSONSchema.version == version)
            .one_or_none()
        )
        if existing:
            assert (
                existing.schema == schema
            ), "Schema ({}, {}) exists, but schema is different.".format(name, version)
            continue
        else:
            db_schema = JSONSchema(**{"name": name, "version": version, "schema": schema})

        session.add(db_schema)


def create_jsonschema_sql_functions(session):
    session.execute(
        """
        -- Copied from https://github.com/gavinwahl/postgres-json-schema/tree/5a257e19a1569a77b82e9182b0b7d9fc8b6f6382
        -- PostgreSQL License

        CREATE OR REPLACE FUNCTION _validate_json_schema_type(type text, data jsonb) RETURNS boolean AS $f$
        BEGIN
        IF type = 'integer' THEN
            IF jsonb_typeof(data) != 'number' THEN
            RETURN false;
            END IF;
            IF trunc(data::text::numeric) != data::text::numeric THEN
            RETURN false;
            END IF;
        ELSE
            IF type != jsonb_typeof(data) THEN
            RETURN false;
            END IF;
        END IF;
        RETURN true;
        END;
        $f$ LANGUAGE 'plpgsql' IMMUTABLE;

        -- Copied from https://github.com/gavinwahl/postgres-json-schema/tree/5a257e19a1569a77b82e9182b0b7d9fc8b6f6382
        -- PostgreSQL License

        CREATE OR REPLACE FUNCTION validate_json_schema(schema jsonb, data jsonb, root_schema jsonb DEFAULT NULL) RETURNS boolean AS $f$
        DECLARE
        prop text;
        item jsonb;
        path text[];
        types text[];
        pattern text;
        props text[];
        BEGIN
        IF root_schema IS NULL THEN
            root_schema = schema;
        END IF;

        IF schema ? 'type' THEN
            IF jsonb_typeof(schema->'type') = 'array' THEN
            types = ARRAY(SELECT jsonb_array_elements_text(schema->'type'));
            ELSE
            types = ARRAY[schema->>'type'];
            END IF;
            IF (SELECT NOT bool_or(_validate_json_schema_type(type, data)) FROM unnest(types) type) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'properties' THEN
            FOR prop IN SELECT jsonb_object_keys(schema->'properties') LOOP
            IF data ? prop AND NOT validate_json_schema(schema->'properties'->prop, data->prop, root_schema) THEN
                RETURN false;
            END IF;
            END LOOP;
        END IF;

        IF schema ? 'required' AND jsonb_typeof(data) = 'object' THEN
            IF NOT ARRAY(SELECT jsonb_object_keys(data)) @>
                ARRAY(SELECT jsonb_array_elements_text(schema->'required')) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'items' AND jsonb_typeof(data) = 'array' THEN
            IF jsonb_typeof(schema->'items') = 'object' THEN
            FOR item IN SELECT jsonb_array_elements(data) LOOP
                IF NOT validate_json_schema(schema->'items', item, root_schema) THEN
                RETURN false;
                END IF;
            END LOOP;
            ELSE
            IF NOT (
                SELECT bool_and(i > jsonb_array_length(schema->'items') OR validate_json_schema(schema->'items'->(i::int - 1), elem, root_schema))
                FROM jsonb_array_elements(data) WITH ORDINALITY AS t(elem, i)
            ) THEN
                RETURN false;
            END IF;
            END IF;
        END IF;

        IF jsonb_typeof(schema->'additionalItems') = 'boolean' and NOT (schema->'additionalItems')::text::boolean AND jsonb_typeof(schema->'items') = 'array' THEN
            IF jsonb_array_length(data) > jsonb_array_length(schema->'items') THEN
            RETURN false;
            END IF;
        END IF;

        IF jsonb_typeof(schema->'additionalItems') = 'object' THEN
            IF NOT (
                SELECT bool_and(validate_json_schema(schema->'additionalItems', elem, root_schema))
                FROM jsonb_array_elements(data) WITH ORDINALITY AS t(elem, i)
                WHERE i > jsonb_array_length(schema->'items')
            ) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'minimum' AND jsonb_typeof(data) = 'number' THEN
            IF data::text::numeric < (schema->>'minimum')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'maximum' AND jsonb_typeof(data) = 'number' THEN
            IF data::text::numeric > (schema->>'maximum')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF COALESCE((schema->'exclusiveMinimum')::text::bool, FALSE) THEN
            IF data::text::numeric = (schema->>'minimum')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF COALESCE((schema->'exclusiveMaximum')::text::bool, FALSE) THEN
            IF data::text::numeric = (schema->>'maximum')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'anyOf' THEN
            IF NOT (SELECT bool_or(validate_json_schema(sub_schema, data, root_schema)) FROM jsonb_array_elements(schema->'anyOf') sub_schema) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'allOf' THEN
            IF NOT (SELECT bool_and(validate_json_schema(sub_schema, data, root_schema)) FROM jsonb_array_elements(schema->'allOf') sub_schema) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'oneOf' THEN
            IF 1 != (SELECT COUNT(*) FROM jsonb_array_elements(schema->'oneOf') sub_schema WHERE validate_json_schema(sub_schema, data, root_schema)) THEN
            RETURN false;
            END IF;
        END IF;

        IF COALESCE((schema->'uniqueItems')::text::boolean, false) THEN
            IF (SELECT COUNT(*) FROM jsonb_array_elements(data)) != (SELECT count(DISTINCT val) FROM jsonb_array_elements(data) val) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'additionalProperties' AND jsonb_typeof(data) = 'object' THEN
            props := ARRAY(
            SELECT key
            FROM jsonb_object_keys(data) key
            WHERE key NOT IN (SELECT jsonb_object_keys(schema->'properties'))
                AND NOT EXISTS (SELECT * FROM jsonb_object_keys(schema->'patternProperties') pat WHERE key ~ pat)
            );
            IF jsonb_typeof(schema->'additionalProperties') = 'boolean' THEN
            IF NOT (schema->'additionalProperties')::text::boolean AND jsonb_typeof(data) = 'object' AND NOT props <@ ARRAY(SELECT jsonb_object_keys(schema->'properties')) THEN
                RETURN false;
            END IF;
            ELSEIF NOT (
            SELECT bool_and(validate_json_schema(schema->'additionalProperties', data->key, root_schema))
            FROM unnest(props) key
            ) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? '$ref' THEN
            path := ARRAY(
            SELECT regexp_replace(regexp_replace(path_part, '~1', '/'), '~0', '~')
            FROM UNNEST(regexp_split_to_array(schema->>'$ref', '/')) path_part
            );
            -- ASSERT path[1] = '#', 'only refs anchored at the root are supported';
            IF NOT validate_json_schema(root_schema #> path[2:array_length(path, 1)], data, root_schema) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'enum' THEN
            IF NOT EXISTS (SELECT * FROM jsonb_array_elements(schema->'enum') val WHERE val = data) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'minLength' AND jsonb_typeof(data) = 'string' THEN
            IF char_length(data #>> '{}') < (schema->>'minLength')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'maxLength' AND jsonb_typeof(data) = 'string' THEN
            IF char_length(data #>> '{}') > (schema->>'maxLength')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'not' THEN
            IF validate_json_schema(schema->'not', data, root_schema) THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'maxProperties' AND jsonb_typeof(data) = 'object' THEN
            IF (SELECT count(*) FROM jsonb_object_keys(data)) > (schema->>'maxProperties')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'minProperties' AND jsonb_typeof(data) = 'object' THEN
            IF (SELECT count(*) FROM jsonb_object_keys(data)) < (schema->>'minProperties')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'maxItems' AND jsonb_typeof(data) = 'array' THEN
            IF (SELECT count(*) FROM jsonb_array_elements(data)) > (schema->>'maxItems')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'minItems' AND jsonb_typeof(data) = 'array' THEN
            IF (SELECT count(*) FROM jsonb_array_elements(data)) < (schema->>'minItems')::numeric THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'dependencies' THEN
            FOR prop IN SELECT jsonb_object_keys(schema->'dependencies') LOOP
            IF data ? prop THEN
                IF jsonb_typeof(schema->'dependencies'->prop) = 'array' THEN
                IF NOT (SELECT bool_and(data ? dep) FROM jsonb_array_elements_text(schema->'dependencies'->prop) dep) THEN
                    RETURN false;
                END IF;
                ELSE
                IF NOT validate_json_schema(schema->'dependencies'->prop, data, root_schema) THEN
                    RETURN false;
                END IF;
                END IF;
            END IF;
            END LOOP;
        END IF;

        IF schema ? 'pattern' AND jsonb_typeof(data) = 'string' THEN
            IF (data #>> '{}') !~ (schema->>'pattern') THEN
            RETURN false;
            END IF;
        END IF;

        IF schema ? 'patternProperties' AND jsonb_typeof(data) = 'object' THEN
            FOR prop IN SELECT jsonb_object_keys(data) LOOP
            FOR pattern IN SELECT jsonb_object_keys(schema->'patternProperties') LOOP
                RAISE NOTICE 'prop %s, pattern %, schema %', prop, pattern, schema->'patternProperties'->pattern;
                IF prop ~ pattern AND NOT validate_json_schema(schema->'patternProperties'->pattern, data->prop, root_schema) THEN
                RETURN false;
                END IF;
            END LOOP;
            END LOOP;
        END IF;

        IF schema ? 'multipleOf' AND jsonb_typeof(data) = 'number' THEN
            IF data::text::numeric % (schema->>'multipleOf')::numeric != 0 THEN
            RETURN false;
            END IF;
        END IF;

        RETURN true;
        END;
        $f$ LANGUAGE 'plpgsql' IMMUTABLE;

        -- Helper function for identifying which schema version some data fulfills. Returns largest version number, or null if no match found.
        CREATE OR REPLACE FUNCTION schema_version(data jsonb, schema_name text, allow_null bool default true) RETURNS int as $f$
        DECLARE
        available_schema_versions int[];
        x int;
        match int;
        BEGIN
            available_schema_versions = ARRAY(SELECT version FROM jsonschema WHERE name = schema_name ORDER BY version DESC);
            FOREACH x in ARRAY available_schema_versions LOOP
                IF validate_json_schema(schema, data) FROM jsonschema where version = x and name = schema_name THEN
                    RETURN x;
                END IF;
            END LOOP;
        IF allow_null IS FALSE THEN
            RAISE EXCEPTION  'schema_name=%, data=% ---- failed to validate against any of the existing schemas', schema_name, data USING ERRCODE='JSONV';
        END IF;
        RETURN NULL;
        END;
        $f$ LANGUAGE 'plpgsql' IMMUTABLE;
        """
    )


def create_schema_triggers(session):
    schema_triggers = [
        {"table": "annotation", "json_column": "annotations", "version_column": "schema_version"},
        {
            "table": "filterconfig",
            "json_column": "filterconfig",
            "version_column": "schema_version",
        },
    ]

    sql_template = """
        CREATE OR REPLACE FUNCTION {table}_schema_version() RETURNS TRIGGER AS $f$
            BEGIN
                NEW.{version_column} = schema_version(NEW.{json_column}, '{table}', false);
                RETURN NEW;
            END;
        $f$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS {table}_schema_version ON {table};
        CREATE TRIGGER {table}_schema_version
        BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW EXECUTE PROCEDURE {table}_schema_version();
        """

    for trigger in schema_triggers:
        session.execute(sql_template.format(**trigger))


if __name__ == "__main__":
    db = DB()
    db.connect()
    update_schemas(db.session)
    db.session.commit()
