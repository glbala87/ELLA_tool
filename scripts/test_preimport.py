import os
import sys
from pathlib import Path
import subprocess
import json


def test_preimport():
    TESTDATA_GENEPANELS = Path("/ella/ella-testdata/testdata/clinicalGenePanels")
    for gp_dir in TESTDATA_GENEPANELS.iterdir():
        if gp_dir.is_dir():
            gp_name, gp_version = gp_dir.name.split("_", 1)
            s = subprocess.check_output(
                [sys.executable, "/ella/scripts/preimport.py"],
                env={
                    "SAMPLE_ID": "",
                    "GENEPANEL_NAME": gp_name,
                    "GENEPANEL_VERSION": gp_version,
                    "PRIORITY": "",
                    "USERGROUP": "",
                    **os.environ,
                },
            )
            d = json.loads(s)
            d["files"] = {k: Path(v) for k, v in d["files"].items()}

            ignore_files = [
                f"{gp_name}_{gp_version}.json",
                "panel_build_log.txt",
                "files_legend.txt",
            ]

            # Check that all files are present, and are equal (except for header line)
            for gp_file in gp_dir.iterdir():
                if gp_file.name in ignore_files:
                    continue
                matching_file = next(x for x in d["files"].values() if x.name == gp_file.name)
                assert matching_file != gp_file, "Same file!"
                with open(gp_file) as f1, open(matching_file) as f2:
                    for i, (line1, line2) in enumerate(zip(f1, f2)):
                        if i == 0 and line1 != line2:
                            assert line1.startswith("#")
                            assert line2.startswith("#")
                        else:
                            assert line1 == line2
