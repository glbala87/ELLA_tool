import json
import re
import jsonschema
from pathlib import Path


FOLDER_FIELDS_RE = re.compile(
    r"(?P<analysis_name>.+[.-](?P<genepanel_name>.+)[-_](?P<genepanel_version>.+))"
)
VCF_FIELDS_RE = re.compile(FOLDER_FIELDS_RE.pattern + r"\.vcf")


class AnalysisConfigData(dict):
    SCHEMA = """
    {
        "definitions": {
            "data": {
                "$id": "#/definitions/submitter",
                "type": "object",
                "required": ["vcf", "technology"],
                "optional": ["ped", "callerName"],
                "additionalProperties": false,
                "properties": {
                    "vcf": {
                        "type": "string"
                    },
                    "ped": {
                        "$oneOf": [
                            {
                                "type": "string"
                            },
                            {
                                "type": "null"
                            }
                        ]
                    },
                    "technology": {
                        "type": "string"
                    },
                    "callerName": {
                        "type": "string"
                    }
                }
            }
        },
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "analysis_config_data",
        "type": "object",
        "required": ["name", "genepanel_name", "genepanel_version", "priority", "data"],
        "optional": ["report", "warnings", "date_requested", "date_analysis_requested"],
        "additionalProperties": false,
        "properties": {
            "name": {
                "type": "string"
            },
            "genepanel_name": {
                "type": "string"
            },
            "genepanel_version": {
                "type": "string"
            },
            "priority": {
                "type": "integer"
            },
            "date_requested": {
                "$oneOf": [
                    { "type": "string", "pattern": "[0-9]{4}-[0-1][0-9]-[0-3][0-9]" },
                    { "type": "null" }
                ]
            },
            "date_analysis_requested": {
                "$oneOf": [
                    { "type": "string", "pattern": "[0-9]{4}-[0-1][0-9]-[0-3][0-9]" },
                    { "type": "null" }
                ]
            },
            "report": {
                "$oneOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "null"
                    }
                ]
            },
            "warnings": {
                "$oneOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "null"
                    }
                ]
            },
            "data": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/data"
                }
            }
        }
    }
    """
    DEFAULTS = {"priority": 1, "report": None, "warnings": None, "data": []}  # type: ignore
    DATA_DEFAULTS = {"technology": "HTS", "ped": None}

    def __init__(self, folder_or_file):
        super().__init__()
        if folder_or_file is None:
            # No data provided: apply defaults only
            self.__apply_defaults()
            return

        folder_or_file = Path(folder_or_file).absolute()
        assert folder_or_file.exists()
        if folder_or_file.is_dir():
            self._root = folder_or_file
            self._init_from_folder(folder_or_file)
            self["warnings"] = self.__load_file(self._root / "warnings.txt")
            self["report"] = self.__load_file(self._root / "report.txt")
        elif (
            folder_or_file.is_file()
            and folder_or_file.suffix == ".vcf"
            or str(folder_or_file).endswith(".vcf.gz")
        ):
            self._root = folder_or_file.parent
            self._init_from_vcf(folder_or_file)
        elif folder_or_file.is_file() and folder_or_file.suffix == ".analysis":
            self._root = folder_or_file.parent
            self._init_from_analysis_file(folder_or_file)
            self["warnings"] = self.__load_file(self._root / "warnings.txt")
            self["report"] = self.__load_file(self._root / "report.txt")
        else:
            raise ValueError(
                "Unable to create AnalysisConfigData from input {}".format(folder_or_file)
            )

    def update(self, d):
        super().update(d)
        self.__absolute_filepaths()
        self.__apply_defaults()
        self.__check_schema()

    def __setitem__(self, k, v):
        self.update({k: v})

    def __check_schema(self):
        schema = json.loads(AnalysisConfigData.SCHEMA)
        jsonschema.validate(self, schema, format_checker=jsonschema.FormatChecker())

    def __apply_defaults(self):
        for k, v in AnalysisConfigData.DEFAULTS.items():
            self.setdefault(k, v)

        for d in self["data"]:
            for k, v in AnalysisConfigData.DATA_DEFAULTS.items():
                d.setdefault(k, v)

    def __absolute_filepaths(self):
        for v in self["data"]:
            for key in ["vcf", "ped"]:
                if key in v and v[key] is not None:
                    if not Path(v[key]).is_absolute():
                        v[key] = str(self._root / v[key])
                    assert Path(v[key]).is_file(), "Unable to find file at {}".format(v[key])

    def __load_file(self, path):
        if path.is_file():
            with open(path, "r") as f:
                return f.read()
        else:
            return None

    def _init_from_legacy_analysis_file(self, filename):
        with open(filename, "r") as f:
            legacy = json.load(f)

        d = {
            "name": legacy["name"],
            "genepanel_name": legacy["params"]["genepanel"].split("_")[0],
            "genepanel_version": legacy["params"]["genepanel"].split("_")[1],
            "data": [{"vcf": next(filename.parent.glob(filename.stem + ".vcf*")).name}],
        }

        if filename.absolute().with_suffix(".ped").is_file():
            d["data"][0]["ped"] = filename.stem + ".ped"

        if "priority" in legacy:
            d["priority"] = int(legacy["priority"])

        for date_key in ["date_requested", "date_analysis_requested"]:
            if date_key in legacy:
                d["date_requested"] = legacy[date_key]

        self.update(d)

    def _init_from_analysis_file(self, filename):

        with open(filename, "r") as f:
            d = json.load(f)

        if "params" in d:
            return self._init_from_legacy_analysis_file(filename)
        else:
            self.update(d)

    def _init_from_vcf(self, vcf):
        matches = re.match(VCF_FIELDS_RE, vcf.name)
        self.update(
            {
                "name": matches.group("analysis_name"),
                "genepanel_name": matches.group("genepanel_name"),
                "genepanel_version": matches.group("genepanel_version"),
                "data": [{"vcf": str(vcf)}],
            }
        )

    def _init_from_folder(self, folder):
        analysis_files = [p.name for p in folder.rglob("*.analysis")]
        assert (
            len(analysis_files) <= 1
        ), "Multiple .analysis-files found in folder {}: {} This is not supported.".format(
            folder, analysis_files
        )
        if len(analysis_files) == 1:
            return self._init_from_analysis_file(folder / analysis_files[0])
        else:
            matches = re.match(FOLDER_FIELDS_RE, folder.name)
            vcfs = sorted([p for p in folder.rglob("*.vcf*")])
            peds = [p for p in folder.rglob("*.ped")]
            assert len(vcfs) >= 1, "Unable to find vcf-file in folder"

            # Match vcfs with peds on filename stem
            vcf_peds = [
                (vcf, next((ped for ped in peds if ped.stem == vcf.stem.split(".")[0]), None))
                for vcf in vcfs
            ]
            self.update(
                {
                    "name": matches.group("analysis_name"),
                    "genepanel_name": matches.group("genepanel_name"),
                    "genepanel_version": matches.group("genepanel_version"),
                    "data": [
                        {"vcf": str(vcf), "ped": str(ped) if ped else None}
                        for (vcf, ped) in vcf_peds
                    ],
                }
            )
