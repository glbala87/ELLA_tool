#!/usr/bin/env python3
from __future__ import annotations

import datetime
import importlib
import re
import sys
from abc import ABC, abstractmethod
from collections import Counter, defaultdict, namedtuple
from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from pathlib import Path
from types import ModuleType
from typing import Any, DefaultDict, Dict, List, NoReturn, Optional, Sequence, Set, Tuple

import click
from api.main import api
from api.schemas.pydantic.v1 import BaseModel, ResourceValidator
from api.schemas.pydantic.v1.resources import gen_api_model
from api.util.types import ResourceMethods
from typing_extensions import TypedDict
from flask.views import MethodViewType
from werkzeug.routing import Rule

API_VERSION = "v1"
ENDPOINT_PREFIX = f"/api/{API_VERSION}"
BASE_PKG = f"api.schemas.pydantic.{API_VERSION}"
DEFAULT_PKG = f"{BASE_PKG}.resources"
DEFAULT_MODEL = "ApiModel"
RESP_FILTER = {"HEAD", "OPTIONS"}
REQ_FILTER = RESP_FILTER | {"GET", "DELETE"}

###


class Error(IntFlag):
    MISSING_PARAMETER = auto()
    BAD_PACKAGE = auto()
    BAD_MODEL = auto()
    BAD_ENDPOINT = auto()
    MISSING_ENDPOINT = auto()
    UNKNOWN = auto()


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}>"

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: List[Any]) -> str:
        # sets how auto() generates the value from the given name
        return name.lower()


class TypingStatus(StrEnum):
    DEFINED = auto()
    TYPED = auto()
    UNTYPED = auto()


class ValidatorTypes(StrEnum):
    REQUEST = auto()
    RESPONSE = auto()


###


class EndpointStats(Counter):
    "Counter for each permutation of ValidatorTypes x TypingStatus"

    def _fetch(self, *, vtype: ValidatorTypes = None, status: TypingStatus = None):
        if vtype:
            target_vtypes = [vtype]
        else:
            target_vtypes = [v for v in ValidatorTypes]
        if status:
            target_status = [status]
        else:
            target_status = [s for s in TypingStatus if s]
        total = 0
        for vt in target_vtypes:
            for st in target_status:
                total += self[(vt, st)]
        return total

    def typed(self):
        return self._fetch(status=TypingStatus.TYPED)

    def untyped(self):
        return self._fetch(status=TypingStatus.UNTYPED)

    def defined(self):
        return self._fetch(status=TypingStatus.DEFINED)

    def requests(self):
        return self._fetch(vtype=ValidatorTypes.REQUEST)

    def responses(self):
        return self._fetch(vtype=ValidatorTypes.RESPONSE)


@dataclass(frozen=True)
class ApiStats:
    endpoints: EndpointStats
    methods: EndpointStats


class BaseStats(TypedDict):
    defined: int
    typed: int
    untyped: int


class AbstractSummary(ABC):
    defined: Set[str]
    typed: Set[str]

    def __repr__(self):
        return f"<{self.__class__.__name__} defined={len(self.defined)} typed={len(self.typed)} status={self.status()}>"

    def __str__(self) -> str:
        return super().__str__()

    @abstractmethod
    def summarize(self):
        ...

    @abstractmethod
    def members(self) -> Sequence[AbstractSummary]:
        ...

    @property
    def untyped(self):
        return self.defined - self.typed

    def status(self):
        if self.members():
            return self._meta_status([m.status() for m in self.members() if m.status()])
        else:
            return self._status()

    def _status(self):
        if not self.defined:
            return None
        elif not self.typed or len(self.defined) > len(self.typed):
            return TypingStatus.UNTYPED
        elif len(self.typed) > len(self.defined):
            raise ValueError(f"More typed values than defined: {self.typed} vs {self.defined}")
        else:
            return TypingStatus.TYPED

    def _meta_status(self, slist: Sequence[AbstractSummary]):
        if any([m is TypingStatus.UNTYPED for m in slist]):
            return TypingStatus.UNTYPED
        elif not slist:
            return None
        elif all([m is TypingStatus.TYPED for m in slist]):
            return TypingStatus.TYPED
        else:
            breakpoint()
            raise ValueError(f"Invalid state, cannot determine status: {self}")


class ValidatorSummary(AbstractSummary):
    typed: Set[str]
    defined: Set[str]

    def __init__(self, *, typed: Set[str] = None, defined: Set[str] = None):
        self.typed = typed if typed else set()
        self.defined = defined if defined else set()

    def members(self):
        return None

    def summarize(self) -> BaseStats:
        return {
            "defined": len(self.defined),
            "typed": len(self.typed),
            "untyped": len(self.untyped),
        }


class EndpointSummary(AbstractSummary):
    rule: str
    validators: Dict[ValidatorTypes, ValidatorSummary]

    def __init__(
        self,
        rule: str,
        request_summary: ValidatorSummary = None,
        response_summary: ValidatorSummary = None,
    ):
        self.rule = rule
        self.validators = {
            ValidatorTypes.REQUEST: request_summary if request_summary else ValidatorSummary(),
            ValidatorTypes.RESPONSE: response_summary if response_summary else ValidatorSummary(),
        }

    def members(self) -> Sequence[AbstractSummary]:
        return list(self.validators.values())

    def summarize(self):
        ts = EndpointStats()
        for vtype, vsumm in self.validators.items():
            ts.update(
                {(vtype, TypingStatus(status)): cnt for status, cnt in vsumm.summarize().items()}
            )
        return ts

    def _get_methods(self, status: TypingStatus) -> Set[str]:
        mlist = set()
        for vtype in self.validators:
            mlist.update([f"{vtype}.{x}" for x in getattr(self.validators[vtype], str(status), [])])
        return mlist

    @property
    def defined(self):
        return self._get_methods(TypingStatus.DEFINED)

    @property
    def typed(self):
        return self._get_methods(TypingStatus.TYPED)

    def add_types(self, val: ResourceValidator, methods: ResourceMethods):
        mset = {str(m) for m in methods.contents}
        vtype = get_vtype(val)
        overlap = self.validators[vtype].typed & mset
        self.validators[vtype].typed |= mset

        return (
            Overlap(endpoint=self.rule, validator_name=val.__name__, methods=", ".join(overlap))
            if overlap
            else None
        )


@dataclass(frozen=True)
class Overlap:
    endpoint: str
    validator_name: str
    methods: str

    def __str__(self) -> str:
        return "\t".join([self.endpoint, self.validator_name, self.methods])


class ApiSummary(AbstractSummary):
    def __init__(self, endpoints: Dict[str, EndpointSummary] = None) -> None:
        if not endpoints:
            endpoints = {}
        self.endpoints = endpoints

    def members(self):
        return self.endpoints

    def summarize(self) -> ApiStats:
        ep_counter = EndpointStats()
        meth_counter = EndpointStats()
        for ep in self.endpoints.values():
            ep_stats = ep.summarize()
            ep_counter.update(
                {
                    (vtype, status): 1
                    for status in TypingStatus
                    for vtype in ValidatorTypes
                    if ep_stats[(vtype, status)] > 0
                }
            )
            meth_counter.update(ep_stats)
        return ApiStats(
            endpoints=ep_counter,
            methods=meth_counter,
        )


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


def get_model(pkg: ModuleType, model_name: str) -> BaseModel:
    try:
        return getattr(pkg, model_name)
    except AttributeError:
        err(f"Could not find {model_name} in {pkg.__name__}", Error.BAD_MODEL)


def get_endpoint_model(master_model: BaseModel, endpoint: str) -> Tuple[str, BaseModel]:
    if not endpoint.startswith(ENDPOINT_PREFIX):
        err(f"Invalid endpoint '{endpoint}'. Must start with {ENDPOINT_PREFIX}", Error.BAD_ENDPOINT)

    for model_name, model_def in master_model.schema()["definitions"].items():
        if model_def.get("description", "").strip() == endpoint:
            return model_name, get_model(sys.modules[master_model.__module__], model_name)
    err(f"No models found for {endpoint}", Error.MISSING_ENDPOINT)


def dump_schema(model: BaseModel, output: Optional[str] = None):
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


def get_vtype(val: ResourceValidator):
    if val.__name__.endswith("Request"):
        return ValidatorTypes.REQUEST
    elif val.__name__.endswith("Response"):
        return ValidatorTypes.RESPONSE
    raise ValueError(f"Invalid Validator class name: {val.name}")


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

    if dump_all:
        model_obj = gen_api_model()
    else:
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
        check_validators(model_obj)
        check_endpoints(model_obj)
        pretty_name = "all"
    elif endpoint:
        pretty_name = endpoint
    else:
        pretty_name = f"{pkg.__name__}.{model_name}"

    output_dest = dump_schema(model_obj, output)
    log(f"Finished writing {pretty_name} schema(s) to {output_dest}")


def check_validators(api_model: BaseModel, model_names: Optional[List[str]] = None):
    errs: DefaultDict[str, List[str]] = defaultdict(list)
    requests = 0
    responses = 0
    for fname, fvalue in api_model.__fields__.items():
        if not hasattr(fvalue.type_, "endpoints") or not fvalue.type_.endpoints:
            errs["missing_endpoints"].append(fvalue.type_.__name__)
        elif fname.endswith("_response"):
            responses += 1
        elif fname.endswith("_request"):
            requests += 1
        else:
            errs["bad_name"].append(fvalue.type_.__name__)

    if errs:
        err_strs = ["\n\t".join([k, *v]) for k, v in errs.items()]
        err("\n".join([f"Validators failed validation:", *err_strs]))
    log(f"Found {requests + responses} validators ({requests} Request, {responses} Response)")


def check_resources():
    import inspect

    class MethodStatus(namedtuple):
        name: ResourceMethods
        rtype: ValidatorTypes

    class EndpointResource(namedtuple):
        route: str
        endpoint: str
        resource: MethodViewType
        defined: Set[MethodStatus]
        typed: Set[MethodStatus]

        def __init__(
            self,
            route: str,
            endpoint: str,
            resource: MethodViewType,
            defined: Optional[Set[MethodStatus]],
            typed: Optional[Set[MethodStatus]],
        ):
            self.route = route
            self.endpoint = endpoint
            self.resource = resource
            self.defined = defined if defined else set()
            self.typed = typed if typed else set()

        @property
        def untyped(self):
            return self.defined - self.typed

    def get_methods(r: MethodViewType):
        m = set(
            [MethodStatus(x, ValidatorTypes.RESPONSE) for x in _get_methods(r.methods, RESP_FILTER)]
        )
        m.update(
            [MethodStatus(x, ValidatorTypes.REQUEST) for x in _get_methods(r.methods, REQ_FILTER)]
        )
        return m

    def _get_methods(mlist: Sequence[str], filter: Set[str]):
        return {m for m in mlist if m not in filter}

    api_model = gen_api_model()
    ep_class: Dict[str, MethodViewType] = {
        ep_name: dict(inspect.getmembers(v)).get("view_class")
        for ep_name, v in api.app.view_functions.items()
    }

    ep_status: Dict[str, EndpointResource] = {}
    r: Rule
    for r in api.app.url_map.iter_rules():
        api_resource = ep_class[r.endpoint]
        ep = ep_status.get(r.rule)
        if not ep:
            ep = EndpointResource(
                route=r.rule,
                endpoint=r.endpoint,
                resource=api_resource,
                defined=get_methods(api_resource),
            )
            ep_status[r.rule] = ep

    for val_field in api_model.__fields__.values():
        ...


def check_endpoints(api_model: BaseModel):
    log("Checking typed endpoints vs API endpoints")

    # set up dict of all defined endpoints
    all_api_endpoints: Dict[str, EndpointSummary] = {
        rule.rule: EndpointSummary(
            rule.rule,
            response_summary=ValidatorSummary(defined=rule.methods - RESP_FILTER),
            request_summary=ValidatorSummary(defined=rule.methods - REQ_FILTER),
        )
        for rule in api.app.url_map._rules
        if re.sub(r"<[^>]+>", "", rule.rule).strip(" /")
    }

    invalid_names: List[str] = []
    invalid_endpoints: List[str] = []
    overlap = defaultdict(set)
    # populate endpoints with validator typing information
    for val_field in api_model.__fields__.values():
        try:
            ValidatorTypes(val_field.name.rsplit("_", 1)[-1])
        except ValueError:
            invalid_names.append(val_field.name)
            continue
        validator: ResourceValidator = val_field.type_

        for endpoint, v in validator.endpoints.items():
            if endpoint not in all_api_endpoints:
                meth_str = ", ".join(str(c) for c in v.contents)
                invalid_endpoints.append(f"{validator.__name__}: {meth_str} - {endpoint}")
                continue
            overlap = all_api_endpoints[endpoint].add_types(validator, methods=v)
            if overlap:
                overlap[endpoint].add(overlap)

    if any([invalid_endpoints, invalid_names, overlap]):
        err_strs = []
        if invalid_names:
            err_strs.append(
                "\n\t".join(
                    [
                        f"Found {len(invalid_names)} invalid Validator names",
                        *invalid_names,
                    ]
                )
            )
        if overlap:
            err_strs.append(
                "\n\t".join(
                    [
                        f"Found {len(overlap)} endpoints with more than one validator for a given method",
                        *[str(o) for ep in overlap for o in overlap[ep]],
                    ]
                )
            )
        if invalid_endpoints:
            err_strs.append(
                "\n\t".join(
                    [f"Found {len(invalid_endpoints)} invalid endpoints", *invalid_endpoints]
                )
            )
        err("\n".join(err_strs))

    api_status = ApiSummary(all_api_endpoints)
    final = api_status.summarize()
    for vtype in ValidatorTypes:
        # response, request
        log(f"{vtype.capitalize()} typing status:")
        for status in TypingStatus:
            # defined, typed, untyped
            sub_key = (vtype, status)
            log(
                f"{status.capitalize(): >7}: {final.endpoints[sub_key]} ({final.methods[sub_key]} methods)"
            )
        log(f"Endpoints missing {vtype} types:")
        for ep in sorted(api_status.endpoints.values(), key=lambda x: x.rule):
            try:
                if ep.validators[vtype].status() is TypingStatus.UNTYPED:
                    log(f"{ep.rule} - {ep.validators[vtype].untyped}")
            except ValueError as e:
                print(e)
                breakpoint()
        print()
    log(
        "\n\t- ".join(
            [
                "Overall status",
                (
                    f"Endpoints typed: {final.endpoints.typed()}/{final.endpoints.defined()} "
                    f"({final.endpoints.typed()/final.endpoints.defined()*100:.02f}%)"
                ),
                (
                    f"Methods typed:   {final.methods.typed()}/{final.methods.defined()} "
                    f"({final.methods.typed()/final.methods.defined()*100:.02f}%)"
                ),
            ]
        )
    )


###

if __name__ == "__main__":
    main()
