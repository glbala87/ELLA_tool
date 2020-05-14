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
                        "type": "string"
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
        "optional": ["report", "warnings"],
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
                "type": "string",
                "format": "date-time"
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
    DEFAULTS = {"priority": 1}
    DATA_DEFAULTS = {"technology": "HTS"}

    def __init__(self, folder_or_file):
        folder_or_file = Path(folder_or_file).absolute()
        assert folder_or_file.exists()
        super().__init__()
        if folder_or_file.is_dir():
            self._root = folder_or_file
            self._init_from_folder(folder_or_file)
            self["warnings"] = self._load_file(self._root / "warnings.txt")
            self["report"] = self._load_file(self._root / "report.txt")
        elif folder_or_file.is_file():
            self._root = folder_or_file.parent
            if folder_or_file.suffix == ".vcf":
                self._init_from_vcf(folder_or_file)
                self["warnings"] = None
                self["report"] = None
            elif folder_or_file.suffix == ".analysis":
                self._init_from_analysis_file(folder_or_file)
                self["warnings"] = self._load_file(self._root / "warnings.txt")
                self["report"] = self._load_file(self._root / "report.txt")
            else:
                raise ValueError(
                    "Unable to create AnalysisConfigData from input {}".format(folder_or_file)
                )
        else:
            raise ValueError(
                "Unable to create AnalysisConfigData from input {}".format(folder_or_file)
            )

        self._absolute_filepaths()
        self._apply_defaults()
        self._check_schema()

    def _check_schema(self):
        schema = json.loads(AnalysisConfigData.SCHEMA)
        jsonschema.validate(self, schema, format_checker=jsonschema.FormatChecker())

    def _apply_defaults(self):
        for k, v in AnalysisConfigData.DEFAULTS.items():
            self.setdefault(k, v)

        for d in self["data"]:
            for k, v in AnalysisConfigData.DATA_DEFAULTS.items():
                d.setdefault(k, v)

    def _absolute_filepaths(self):
        for v in self["data"]:
            if not Path(v["vcf"]).is_absolute():
                v["vcf"] = str(self._root / v["vcf"])
            assert Path(v["vcf"]).is_file(), "Unable to find file at {}".format(v["vcf"])
            if "ped" in v and not Path(v["ped"]).is_absolute():
                v["ped"] = str(self._root / v["ped"])

            if "ped" in v:
                assert Path(v["ped"]).is_file(), "Unable to find file at {}".format(v["ped"])

    def _load_file(self, path):
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
            "data": [{"vcf": filename.stem + ".vcf"}],
        }
        if Path(filename.stem + ".ped").is_file():
            d["data"][0]["ped"] = filename.stem + ".ped"

        if "priority" in legacy:
            d["priority"] = int(legacy["priority"])

        if "date_requested" in legacy:
            d["date_requested"] = legacy["date_requested"]

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
            vcfs = [p.name for p in folder.rglob("*.vcf")]
            assert len(vcfs) >= 1
            self.update(
                {
                    "name": matches.group("analysis_name"),
                    "genepanel_name": matches.group("genepanel_name"),
                    "genepanel_version": matches.group("genepanel_version"),
                    "data": [{"vcf": str(vcf)} for vcf in vcfs],
                }
            )


if __name__ == "__main__":

    # Add custom YAML constructors
    file = "/ella/src/vardb/testdata/analyses/default/HG002-Trio.Mendeliome_v01/HG002-Trio.Mendeliome_v01.analysis"
    d1 = AnalysisConfigData(file)
    print(d1)

    folder = "/ella/src/vardb/testdata/analyses/default/HG002-Trio.Mendeliome_v01"
    d2 = AnalysisConfigData(folder)
    print(d2)
    assert d1 == d2

    file = "/ella/src/vardb/testdata/analyses/default/HG002-Trio.Mendeliome_v01/HG002-Trio.Mendeliome_v01.vcf"
    d3 = AnalysisConfigData(file)
    print(d3)

    file = "/ella/src/vardb/testdata/analyses/default/brca_long_variants.HBOCUTV_v01/brca_long_variants.HBOCUTV_v01.analysis"
    d4 = AnalysisConfigData(file)
    print(d4)

    # class AnalysisConfigLoader(yaml.SafeLoader):
    #     pass
    # AnalysisConfigLoader.add_constructor("!contents", lambda loader, node: file_constructor(loader, node, contents=True))

    # d = AnalysisConfigData(foo="bar", baz="dabla")
