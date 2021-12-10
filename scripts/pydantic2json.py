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


###

if __name__ == "__main__":
    main()
