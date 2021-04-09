import glob
from pathlib import Path
import os
import requests

if __name__ == "__main__":
    annotation_service_url = os.environ["ANNOTATION_SERVICE"]
    vcf_files = [Path(x) for x in glob.glob("analyses/*/*/*.vcf")]
    for path in vcf_files:
        if not path.is_file():
            continue
        print(f"Processing {path}")
        with path.open("rt") as existing:
            unannotated = []

            for l in existing:
                l = l.rstrip("\n")
                if l.startswith("##INFO") or l.startswith("##VEP"):
                    continue
                elif l.startswith("#"):
                    unannotated.append(l)
                else:
                    ls = l.split("\t")
                    ls[7] = "."
                    unannotated.append("\t".join(ls))
        response = requests.request(
            "POST",
            f"{annotation_service_url}/api/v1/annotate?wait=True",
            json={"input": "\n".join(unannotated)},
        )
        if response.status_code != 200:
            print(f"Failed re-annotation of {path}")
            continue
        with path.open("wt") as f:
            f.write(response.text)

