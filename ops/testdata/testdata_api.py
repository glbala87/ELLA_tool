#!/usr/bin/env python3

import datetime
import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

from flask import Flask, make_response
from flask_restful import Api, Resource, reqparse
from pydantic import BaseModel, Field
from pydantic.json import pydantic_encoder

from git import GitProcess as FinishedProcess

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
REPO_ROOT = Path(__file__).absolute().parents[2]
TESTDATA_DIR = REPO_ROOT / "ella-testdata"
RESET_SCRIPT = REPO_ROOT / "ops" / "testdata" / "reset-testdata.py"
SUPERVISOR_CFG = REPO_ROOT / "ops" / "dev" / "supervisor.cfg"

parser = reqparse.RequestParser()
parser.add_argument("testset")


###

app = Flask("testdata-server")
app.config["RESTFUL_JSON"] = {
    "default": pydantic_encoder,
    "separators": (",", ":"),
    "indent": None,
}
api = Api(app)

###


class HealthcheckStatus(Enum):
    OK = "OK"
    LOADING = "LOADING"
    DOWN = "DOWN"

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class HealthcheckTarget:
    healthy: bool
    details: FinishedProcess

    @property
    def name(self):
        return Path(self.details.args[0]).name

    def __bool__(self):
        return self.healthy


class HealthcheckResponse(BaseModel):
    status: HealthcheckStatus
    details: Dict[str, HealthcheckTarget]


class ApiResponse(BaseModel):
    message: Union[str, BaseModel]
    status: int = 200
    ts: str = Field(default_factory=datetime.datetime.now)
    error: Optional[Dict[str, Any]] = None


###


@api.representation("application/json")
def output_json(data, code: int, headers: Optional[Dict[str, Any]] = None):
    data_obj = ApiResponse(**data, status=code)
    resp = make_response(data_obj.json(exclude_none=True), code)
    resp.headers.extend(headers or {})
    return resp


###


def _reset_testdata(action: str, testset: Optional[str]):
    cmd = [str(RESET_SCRIPT), action]
    if testset:
        cmd.extend(["--testset", testset])
    proc = FinishedProcess.load(subprocess.run(cmd, capture_output=True))
    if proc.returncode != 0:
        logging.error(f"reset failed while running: '{cmd}'")
        logging.error(f"stdout: {proc.stdout}")
        logging.error(f"stderr: {proc.stderr}")
        return {
            "message": f"{action} with testset {testset or 'default'} failed",
            "error": vars(proc),
        }, 500
    return {
        "message": f"database {action} with testset {testset or 'default'} complete",
    }, 200


def _postgres_ok():
    proc = FinishedProcess.load(subprocess.run(["/usr/bin/pg_isready"], capture_output=True))
    is_healthy = proc.returncode == 0
    return HealthcheckTarget(healthy=is_healthy, details=proc)


def _supervisor_ok():
    proc = FinishedProcess.load(
        subprocess.run(
            [f"supervisorctl", "-c", str(SUPERVISOR_CFG), "status", "dbreset"],
            capture_output=True,
        )
    )
    is_healthy = "EXITED" in proc.output()
    return HealthcheckTarget(healthy=is_healthy, details=proc)


class ResetTestdata(Resource):
    def post(self):
        args: Dict[str, Any] = parser.parse_args()
        return _reset_testdata("reset", args.get("testset"))


class DumpTestdata(Resource):
    def post(self):
        args: Dict[str, Any] = parser.parse_args()
        if not args.get("testset"):
            return {"message": "Required parameter is missing or empty: testset"}, 400
        return _reset_testdata("dump", args["testset"])


class CleanTestdata(Resource):
    # removes all local dumps
    def post(self):
        proc = FinishedProcess.load(
            subprocess.run("git clean -xdf".split(), cwd=TESTDATA_DIR, capture_output=True),
            cwd=REPO_ROOT,
        )

        if proc.returncode != 0:
            return {
                "message": f"clean failed returned non-zero: {proc.returncode}",
                "error": proc,
            }, 500

        return {"message": proc.output() or "nothing to remove"}


class Healthcheck(Resource):
    def get(self):
        status_checks = {x.name: x for x in [_supervisor_ok(), _postgres_ok()]}
        if not status_checks["pg_isready"].healthy:
            status = HealthcheckStatus.DOWN
            code = 500
        elif not status_checks["supervisorctl"].healthy:
            status = HealthcheckStatus.LOADING
            code = 503
        else:
            status = HealthcheckStatus.OK
            code = 200

        return {"message": HealthcheckResponse(status=status, details=status_checks)}, code


api.add_resource(DumpTestdata, "/database/dump")
api.add_resource(ResetTestdata, "/database/reset")
api.add_resource(Healthcheck, "/healthcheck")
api.add_resource(CleanTestdata, "/clean")

###

if __name__ == "__main__":
    app.run(port=23232, host="0.0.0.0", debug=True, use_debugger=False)
