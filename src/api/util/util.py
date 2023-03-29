import atexit
import collections.abc
import datetime
import json
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Type

import pytz
from api import ApiError, app, db
from api.config import config, get_user_config
from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.common import SearchFilter
from api.schemas.pydantic.v1.config import UserConfig
from api.util.types import StrDict
from api.util.useradmin import get_usersession_by_token
from flask import Response, g, request
import flask
from jsonschema import Draft7Validator, RefResolver, validate
from pydantic.error_wrappers import ValidationError
from pydantic.json import pydantic_encoder
from vardb.datamodel.log import ResourceLog

log = app.logger

JSON_SCHEMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "../schemas/jsonschemas/")
)


def jsonschema_validate(schema_path, data, base_schema_path=None):
    """
    Validates data according to provided schema.

    If base_schema_path is provided, it supports referencing relative schemas
    by using { "$ref": "file://anotherSchema.json" }
    which will be relative to base_schema_path
    """

    with open(schema_path) as f:
        schema = json.load(f)

    if not base_schema_path:
        validate(instance=data, schema=schema)
    else:

        def jsonschema_handler(uri):
            """
            Handles resolving relative file:// paths, prepending
            the local base_schema_path
            """
            resolve_schema_path = Path(uri.replace("file://", ""))
            if resolve_schema_path.is_absolute():
                return json.loads(resolve_schema_path.read_text())
            else:
                local_path = Path(base_schema_path) / resolve_schema_path
                return json.loads(local_path.read_text())

        resolver = RefResolver.from_schema(schema, handlers={"file": jsonschema_handler})
        validator = Draft7Validator(schema, resolver=resolver)
        validator.check_schema(schema)
        validator.validate(data)


# https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(destination: Dict, src: Mapping):
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param destination: dict onto which the merge is executed
    :param src: dct merged into dct
    :return: None
    """
    if not src:
        return
    for k, v in src.items():
        if (
            k in destination
            and isinstance(destination[k], dict)
            and isinstance(src[k], collections.abc.Mapping)
        ):
            dict_merge(destination[k], src[k])
        else:
            destination[k] = src[k]


def query_print_table(sa_query, print_function=None):
    """
    Prints SQLAlchemy query as table to terminal.

    Used for debugging and adding examples to code comments.
    """
    if print_function is None:
        print_function = print

    column_names = [e["name"] for e in sa_query.column_descriptions]
    data = sa_query.all()
    column_width = {k: len(k) for k in column_names}
    for row in data:
        for name, cell in zip(column_names, row):
            cell_len = len(str(cell))
            if cell_len > column_width[name]:
                column_width[name] = cell_len

    h_divider = "-" * (sum(column_width.values()) + len(column_width) * 3 - 1)

    print_function("┌" + h_divider + "┐")
    row_format = "| "
    for name in column_names:
        row_format += "{:<" + str(column_width[name]) + "} | "

    print_function(row_format.format(*column_names))

    print_function("|" + h_divider + "|")
    for r in data:
        print_function(row_format.format(*[str(ri) for ri in r]))
    print_function("└" + h_divider + "┘")


def error(msg, code):
    return {"error": msg, "status": code}, code


def rest_filter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        kwargs = _add_kwarg(
            load_func=json.loads,
            old_kwargs=kwargs,
            req=request,
            arg_name="q",
            new_kwarg="rest_filter",
        )
        return func(*args, **kwargs)

    return inner


def search_filter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        kwargs = _add_kwarg(
            load_func=SearchFilter.parse_raw,
            old_kwargs=kwargs,
            req=request,
            arg_name="s",
            new_kwarg="search_filter",
        )
        return func(*args, **kwargs)

    return inner


def link_filter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        kwargs = _add_kwarg(
            load_func=json.loads,
            old_kwargs=kwargs,
            req=request,
            arg_name="link",
            new_kwarg="link_filter",
        )
        return func(*args, **kwargs)

    return inner


def _add_kwarg(
    *,
    req: Optional[flask.Request],
    old_kwargs: Dict[str, Any],
    arg_name: str,
    new_kwarg: str,
    load_func: Callable = None,
):
    if req:
        val = req.args.get(arg_name)
        if val and load_func:
            val = load_func(val)
    else:
        val = None
    old_kwargs[new_kwarg] = val
    return old_kwargs


def populate_g_logging():
    g.log_exclude = False
    g.log_hide_payload = False
    g.log_hide_response = True  # We only store response for certain resources due to size concerns


def log_request(statuscode, response=None):
    duration = int(time.time() * 1000.0 - g.request_start_time)
    remote_addr = request.remote_addr
    payload = None
    payload_size = 0
    response_data = None
    response_size = 0
    usersession_id = g.usersession_id if hasattr(g, "usersession_id") else None
    if response:
        response_size = int(response.headers.get("Content-Length", 0))
        if not g.log_hide_response:
            response_data = response.get_data()
    if request.method in ["PUT", "POST", "PATCH", "DELETE"]:
        if not g.log_hide_payload:
            payload = request.get_data().decode()
            payload_size = int(request.headers.get("Content-Length", 0))
        if not app.testing:  # don't add noise to console in tests, see tests.util.FlaskClientProxy
            log.warning(
                "{usersession_id} - {method} - {endpoint} - {json} - {response_size} - {duration}ms".format(
                    usersession_id=usersession_id,
                    method=request.method,
                    endpoint=request.url,
                    json=(payload if payload else "[PAYLOAD HIDDEN]"),
                    response_size=response_size,
                    duration=duration,
                )
            )

    if not g.log_exclude:
        rl = ResourceLog(
            usersession_id=usersession_id,
            remote_addr=remote_addr,
            method=request.method,
            resource=request.path,
            query=request.query_string.decode(),
            response=response_data,
            response_size=response_size,
            payload=payload,
            payload_size=payload_size,
            statuscode=statuscode,
            duration=duration,
        )
        db.session.add(rl)


def logger(exclude=False, hide_payload=False, hide_response=True):
    def _logger(func):
        @wraps(func)
        def inner(*args, **kwargs):
            g.log_exclude = exclude
            g.log_hide_payload = hide_payload
            g.log_hide_response = hide_response
            return func(*args, **kwargs)

        return inner

    return _logger


def provide_session(func):
    @wraps(func)
    def inner(*args, **kwargs):
        kwargs["session"] = db.session
        try:
            return func(*args, **kwargs)
        except Exception:
            db.session.rollback()
            db.session.remove()
            raise
        finally:
            db.session.remove()

    return inner


def paginate(func):
    @wraps(func)
    def inner(*args, **kwargs):
        page = None
        if request:
            page = request.args.get("page")
        if page is None:
            page = 1
        else:
            page = int(page)
        per_page = None
        if request:
            per_page = request.args.get("per_page")
        if per_page is not None:
            per_page = int(per_page)
            if per_page > 50:
                per_page = 50
        else:
            per_page = 10000  # FIXME: Leave at high value until we add pagination in frontend
        limit = request.args.get("limit")
        if limit:
            limit = int(limit)

        kwargs["page"] = page
        kwargs["per_page"] = per_page
        kwargs["limit"] = limit
        result, total = func(*args, **kwargs)
        response_headers = dict()
        if total is not None:
            response_headers["Total-Count"] = total
            total_pages = total // per_page + (1 if total % per_page > 0 else 0)
            if total_pages == 0:
                total_pages = 1
            response_headers["Total-Pages"] = total_pages
        response_headers["Page"] = page
        response_headers["Per-Page"] = per_page
        return result, 200, response_headers

    return inner


def request_json(
    *,
    required_fields: Optional[List[str]] = None,
    allowed_fields: Optional[List[str]] = None,
    strict: bool = False,
    field_map: Mapping[str, List[str]] = None,
    jsonschema: Optional[str] = None,
    model: Optional[Type[BaseModel]] = None,
):
    """
    Decorator: Checks flasks's request (root) json object for 'required'
    fields before passing on the data to the function.

    required_fields: if set, all of these must be present in the Request.get_json() object
        - @request_json(required_fields=["allele_id", "user_id"])

    allowed_fields: if set, the fields will be included if available but not fail if missing. forces strict.
        - @request_json(
            required_fields=["allele_id", "user_id"],
            allowed_fields=["comment", "genepanel"]
        )

    strict: if True, only required/optional fields are passed on

    field_map: a dict of keys whose values are used to filter the keys of that name in Request.get_json() object
        - @request_json(
            required_keys=["user", "content"],
            field_map={
                "user": ["user_id", "name"],
                "content": ["allele_id", "annotation"],
            }
        )

    jsonschema: name of a jsonschema file to use for validating the Request.get_json() object
        - @request_json(jsonschema="workflowActionFinalizeAllelePost.json")

    model: a pydantic class to validate/process the Request.get_json() object
        - @request_json(model=CreateInterpretationLog)

    If no keywords are used, the full response is passed on unaltered. Please, please don't do this.

    example input data:
        {
            "user": {"id": 4, "name": "Erik", "address": "Parkveien"},
            "content": {"mode": "weak", "allele_id": 34, "annotation": 44, "archived": true}
        }
    """

    # used by request_json to process an array of dicts
    def _filter_array_content(source_array: List[Dict[str, Any]]):
        assert required_fields is not None and allowed_fields is not None
        include_fields = set(required_fields + allowed_fields)

        filtered_data = []
        for d in source_array:
            _check_required(d)
            filtered_data.append(
                {k: v for k, v in d.items() if strict is False or k in include_fields}
            )
        return filtered_data

    def _check_required(data: StrDict):
        if required_fields:
            for f in required_fields:
                if data.get(f) is None:
                    raise ApiError("Missing or empty required field {} in provided data.".format(f))

    def array_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            data = request.get_json()
            convert_data = not isinstance(data, list)

            # always parse as list
            if convert_data:
                data = [data]

            validated = _filter_array_content(data)

            # revert to non-list if appropriate
            if convert_data:
                validated = validated[0]
            kwargs["data"] = validated

            return func(*args, **kwargs)

        return inner

    def dict_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            assert field_map, required_fields
            data: Dict = request.get_json()
            _check_required(data, required_fields)

            validated = {}
            for data_key in data.keys():
                if data_key in field_map:
                    validated[data_key] = _filter_array_content(data[data_key])
            kwargs["data"] = validated

            return func(*args, **kwargs)

        return inner

    def jsonschema_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            data = request.get_json()
            jsonschema_validate(
                os.path.join(JSON_SCHEMA_PATH, jsonschema), data, base_schema_path=JSON_SCHEMA_PATH
            )
            kwargs["data"] = data
            return func(*args, **kwargs)

        return inner

    def noop_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            kwargs["data"] = request.get_json()
            return func(*args, **kwargs)

        return inner

    def pydantic_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            assert model
            kwargs["data"] = model.parse_obj(request.get_json())
            return func(*args, **kwargs)

        return inner

    if jsonschema:
        assert not any([required_fields, allowed_fields, field_map, model])
        return jsonschema_wrapper
    elif model:
        assert not any([required_fields, allowed_fields, field_map, jsonschema])
        return pydantic_wrapper
    else:
        if required_fields is None:
            required_fields = []
        if allowed_fields is None:
            allowed_fields = []
        else:
            strict = True
        if field_map:
            return dict_wrapper
        else:
            if not required_fields and not allowed_fields:
                return noop_wrapper
            else:
                return array_wrapper


def populate_g_user():
    g.user = None
    g.usersession_id = None
    token = request.cookies.get("AuthenticationToken")
    if token is None:
        return

    user_session = get_usersession_by_token(db.session, token)

    if user_session:
        user_session.lastactivity = datetime.datetime.now(pytz.utc)
        db.session.commit()
        g.usersession_id = user_session.id
        g.user = user_session.user


def authenticate(
    user_config: bool = False,
    usersession: bool = False,
    optional: bool = False,
    pydantic: bool = False,
):
    """
    Decorator that works in conjunction with flask's 'g' object
    in a before_request trigger, in order to auth the user as
    soon as request is processed.

    See populate_g_user().
    """

    def _authenticate(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if usersession:
                kwargs["usersession_id"] = g.usersession_id

            if g.user:
                # Logged in
                kwargs["user"] = g.user

                # Merge users config
                if user_config:
                    kwargs["user_config"] = get_user_config(
                        config, g.user.group.config, g.user.config
                    )
                    if pydantic:
                        try:
                            kwargs["user_config"] = UserConfig.parse_obj(kwargs["user_config"])
                        except ValidationError:
                            raise SyntaxError(
                                f"Failed to load user_config: {json.dumps(kwargs['user_config'], default=pydantic_encoder)}"
                            )
                return func(*args, **kwargs)
            else:
                # Not logged in
                if optional:
                    if user_config:
                        kwargs["user_config"] = None
                    return func(*args, **kwargs)
                else:
                    return Response(
                        "Authentication required",
                        403,
                        {"WWWAuthenticate": 'Basic realm="Login Required"'},
                    )

        return inner

    return _authenticate


def get_nested(dct, keys, default=None):
    if not dct or not isinstance(dct, dict):
        return default
    for i, key in enumerate(keys):
        try:
            dct = dct[key]
        except KeyError:
            return default
        if i == len(keys) - 1:  # at end
            return dct
        if not isinstance(dct, dict):
            return default
    return default


def Timer():
    """
    Simple utility timer

    Usage:
    > timeit = Timer()
    > timeit("sleep 1")
    > sleep(1)
    > timeit("sleep 2")
    sleep 1: 1.000s
    > sleep(2)
    > exit()
    sleep 2: 2.000s
    """

    class timeit(object):
        description = None
        starttime = None

        def __init__(self, descr):
            timeit.reset_timer(descr)

        @classmethod
        def reset_timer(cls, descr):
            cls.stop_timer()
            cls.description = descr
            cls.starttime = time.time()

        @classmethod
        def stop_timer(cls):
            if cls.description is not None:
                end_time = time.time()
                print(f"{cls.description}: {end_time - cls.starttime:.4f}s")
                cls.description = None
                cls.starttime = None

    atexit.register(timeit.stop_timer)
    return timeit


def str2intlist(val: str, *, sep=",", allow_none: bool = False) -> List[int]:
    if val is None:
        if allow_none:
            return []
        raise ValueError("Can't turn None into List[int]")
    return [int(v.strip()) for v in val.split(sep) if v.strip()]


def from_camel(val: str):
    """converts camelCase to snake_case"""

    # word boundaries at shift from lower to upper case e.g., camel^Case
    # or upper to lower if several uppercase characters in a row e.g., UPPER^Lower
    parts = []
    p_start = 0
    last_idx = len(val) - 1
    for prev, c in enumerate(val[1:], 0):
        i = prev + 1
        if c.islower() ^ val[prev].islower() and prev > 0:
            # case shift
            if c.isupper():
                # case[B]reak
                parts.append(val[p_start:i])
                p_start = i
            elif val[prev - 1].isupper():
                # SOMEB[r]eak
                parts.append(val[p_start:prev])
                p_start = prev

        # end of string
        if i == last_idx:
            parts.append(val[p_start:])

    return "_".join([x.lower() for x in parts])
