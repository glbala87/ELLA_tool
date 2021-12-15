#!/usr/bin/env python3
from __future__ import annotations

import datetime
import importlib
import sys
from enum import IntFlag, auto
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, NoReturn, Optional, Tuple

import click
from api.schemas.pydantic.v1 import PydanticBase
from api.main import api


API_VERSION = "v1"
ENDPOINT_PREFIX = f"/api/{API_VERSION}"
BASE_PKG = f"api.schemas.pydantic.{API_VERSION}"
DEFAULT_PKG = f"{BASE_PKG}.resources"
DEFAULT_MODEL = "ApiModel"

###


class Error(IntFlag):
    MISSING_PARAMETER = auto()
    BAD_PACKAGE = auto()
    BAD_MODEL = auto()
    BAD_ENDPOINT = auto()
    MISSING_ENDPOINT = auto()
    UNKNOWN = auto()


###


def err(msg: str, exit_code: Error = Error.UNKNOWN) -> NoReturn:
    print(msg, file=sys.stderr)
    exit(exit_code)


def log(msg: str):
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}", file=sys.stderr)


def load_package(pkg_name: str):
    try:
        return importlib.import_module(pkg_name)
    except ImportError:
        err(f"Could not find schema module: {pkg_name}", Error.BAD_PACKAGE)


def get_model(pkg: ModuleType, model_name: str) -> PydanticBase:
    try:
        return getattr(pkg, model_name)
    except AttributeError:
        err(f"Could not find {model_name} in {pkg.__name__}", Error.BAD_MODEL)


def get_endpoint_model(master_model: PydanticBase, endpoint: str) -> Tuple[str, PydanticBase]:
    if not endpoint.startswith(ENDPOINT_PREFIX):
        err(f"Invalid endpoint '{endpoint}'. Must start with {ENDPOINT_PREFIX}", Error.BAD_ENDPOINT)

    for model_name, model_def in master_model.schema()["definitions"].items():
        if model_def.get("description", "").strip() == endpoint:
            return model_name, get_model(sys.modules[master_model.__module__], model_name)
    err(f"No models found for {endpoint}", Error.MISSING_ENDPOINT)


def dump_schema(model: PydanticBase, output: Optional[str] = None):
    print_kwargs: Dict[str, Any] = {}
    if output:
        if not output.endswith(".json"):
            output += ".json"
        output_file = Path(output)
        if output_file.exists():
            log(f"Overwriting existing output file {output}")
        print_kwargs["file"] = output_file.open("wt")

    print(model.schema_json(indent=2), **print_kwargs)
    if print_kwargs.get("file"):
        print_kwargs["file"].close()

    return str(output_file.resolve()) if output else "stdout"


###


@click.command(help="Generates JSON Schema files based Pydantic models")
@click.option("--model", "-m", help=f"specific model to export. can omit leading {BASE_PKG}")
@click.option(
    "--endpoint",
    "-e",
    metavar=f"{ENDPOINT_PREFIX}/...",
    help="dump model used for a specific API endpoint",
)
@click.option("--all", "dump_all", is_flag=True, default=False, help="dump all models/endpoints")
@click.option("--output", "-o", help="dump to specified file instead of stdout")
def main(
    model: Optional[str] = None,
    endpoint: Optional[str] = None,
    dump_all: bool = False,
    output: Optional[str] = None,
) -> None:
    if not any([model, endpoint, dump_all]):
        err(
            f"You must specify schema(s) to dump with --model, --endpoint or --all",
            Error.MISSING_PARAMETER,
        )

    if model:
        if not model.startswith(BASE_PKG):
            model = f"{BASE_PKG}.{model}"
        pkg_name = model[: model.rindex(".")]
        model_name = model[model.rindex(".") + 1 :]
    else:
        pkg_name = DEFAULT_PKG
        model_name = DEFAULT_MODEL

    pkg = load_package(pkg_name)
    model_obj = get_model(pkg, model_name)
    if endpoint:
        model_name, model_obj = get_endpoint_model(model_obj, endpoint)

    if dump_all:
        check_validators()
        check_endpoints()
        pretty_name = "all"
    elif endpoint:
        pretty_name = endpoint
    else:
        pretty_name = f"{pkg.__name__}.{model_name}"

    output_dest = dump_schema(model_obj, output)
    log(f"Finished writing {pretty_name} schema(s) to {output_dest}")


def check_validators(model_names: Optional[List[str]] = None):
    import api.schemas.pydantic.v1.resources as pr

    if not model_names:
        model_names = [k for k in dir(pr) if k.endswith("Response") or k.endswith("Request")]
    missing = [m for m in model_names if m not in pr.ApiModel.__annotations__.values()]

    if missing:
        missing_str = ", ".join(missing)
        err(f"Found {len(missing)} validators not assigned to ApiModel: {missing_str}")
    log(f"Found {len(model_names)} Response/Request validators")


def check_endpoints():
    log("Checking typed endpoints vs API endpoints")
    import api.schemas.pydantic.v1.resources as pr

    all_api_endpoints = {
        rule.rule: rule.methods - {"HEAD", "OPTIONS"} for rule in api.app.url_map._rules
    }

    all_payload_endpoints = {
        rule: methods - {"GET", "DELETE"}
        for rule, methods in all_api_endpoints.items()
        if methods - {"GET"}
    }

    response_names = [k for k in dir(pr) if k.endswith("Response")]
    request_names = [k for k in dir(pr) if k.endswith("Request")]
    from collections import defaultdict

    typed_endpoints = defaultdict(set)
    for resp_name in response_names:
        for endpoint, v in getattr(pr, resp_name).endpoints.items():
            # endpoint = re.sub(r"<.*?:", "<", k)
            methods = set(x.name for x in v.contents)
            typed_endpoints[endpoint] |= methods

    missing_typing = {
        k: v - typed_endpoints.get(k, set())
        for k, v in all_api_endpoints.items()
        if v - typed_endpoints.get(k, set())
    }

    log(
        f"Total: {len(all_api_endpoints)} ({len(sum((list(x) for x in all_api_endpoints.values()), []))} methods)."
    )
    log(
        f"Typed: {len(typed_endpoints)} ({len(sum((list(x) for x in typed_endpoints.values()), []))} methods)"
    )
    log(
        f"Untyped: {len(missing_typing)} ({len(sum((list(x) for x in missing_typing.values()), []))} methods)"
    )

    log("Endpoints missing response type:")
    for k, v in missing_typing.items():
        log(f"{k}: {v}")

    not_an_endpoint = set(typed_endpoints.keys()) - set(all_api_endpoints)
    if not_an_endpoint:
        err(f"Typed endpoint(s) not part of the API: {not_an_endpoint}")

    typed_request_endpoints = defaultdict(set)
    for req_name in request_names:
        for endpoint, v in getattr(pr, req_name).endpoints.items():
            # endpoint = re.sub(r"<.*?:", "<", k)
            methods = set(x.name for x in v.contents)
            typed_request_endpoints[endpoint] |= methods

    missing_request_typing = {
        k: v - typed_request_endpoints.get(k, set())
        for k, v in all_payload_endpoints.items()
        if v - typed_request_endpoints.get(k, set())
    }

    log(
        f"Total: {len(all_payload_endpoints)} ({len(sum((list(x) for x in all_payload_endpoints.values()), []))} methods)."
    )
    log(
        f"Typed: {len(typed_request_endpoints)} ({len(sum((list(x) for x in typed_request_endpoints.values()), []))} methods)"
    )
    log(
        f"Untyped: {len(missing_request_typing)} ({len(sum((list(x) for x in missing_request_typing.values()), []))} methods)"
    )

    log("Endpoints missing request type:")
    for k, v in missing_request_typing.items():
        log(f"{k}: {v}")

    not_a_payload_endpoint = set(typed_request_endpoints.keys()) - set(all_payload_endpoints)
    if not_a_payload_endpoint:
        err(f"Typed endpoint(s) not part of the API: {not_a_payload_endpoint}")


###

if __name__ == "__main__":
    main()
