import argparse
import os
import urllib.request
import urllib.error
import urllib.parse
import json
import subprocess

TO_STRIP = ["##INFO", "##GATKCommandLine", "##reference", "##VEP", "##source", "##VEP", "##SnpEff"]
ANNOTATION_SERVICE_URL = "http://localhost:6000"


def strip(filename):
    new_data = []
    with open(filename, "r") as f:
        iter_f = iter(f)
        for l in iter_f:
            if l.startswith("#CHROM"):
                new_data.append(l)
                break

            if any(l.startswith(s) for s in TO_STRIP):
                continue
            else:
                new_data.append(l)

        for l in iter_f:
            record = l.split("\t")
            record[7] = "."
            record = "\t".join(record)
            new_data.append(record)

    return "".join(new_data)


def annotate(inputfile):
    assert os.path.isfile(inputfile)
    data = subprocess.check_output("vcf-sort %s" % inputfile, shell=True)
    data = data.rstrip("\n")
    if not data.startswith("##fileformat"):
        data = "##fileformat=VCFv4.1\n" + data

    resp = urllib.request.urlopen(
        os.path.join(ANNOTATION_SERVICE_URL, "annotate"), data=json.dumps({"vcf": data})
    )
    task_id = json.loads(resp.read())["task_id"]
    print(("Started annotation with task_id=", task_id))
    resp = urllib.request.urlopen(os.path.join(ANNOTATION_SERVICE_URL, "process", task_id))
    resp = json.loads(resp.read())
    assert resp["status"] == "SUCCESS"
    return resp["data"]


def main(command, inputfile, outputfile):
    if command == "strip":
        data = strip(inputfile)
    elif command == "annotate":
        data = annotate(inputfile)
    else:
        raise RuntimeError("Unknown command %s" % command)

    if outputfile is not None:
        with open(outputfile, "w") as f:
            f.write(data)
    else:
        print(data)


def get_vcf_map():
    vcf_map = []
    for dirpath, subdirs, files in os.walk("analyses/"):
        for f in files:
            if f.endswith(".vcf"):
                fullpath = os.path.join(dirpath, f)
                assert os.path.isfile(fullpath)
                if not os.path.islink(fullpath):
                    gp_name, gp_version = f.split(".")[1].split("_")
                    if gp_name in ["HBOC", "HBOCUTV"]:
                        unannotated_filename = ".".join(f.split(".")[::2])
                    else:
                        unannotated_filename = f
                    unannotated_path = os.path.join("unannotated", unannotated_filename)
                    vcf_map.append((fullpath, unannotated_path))
    return vcf_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strip", action="store_true")
    parser.add_argument("--annotate", action="store_true")
    parser.add_argument("-f", help="File to run command on")
    parser.add_argument("-o", help="Output file")
    parser.add_argument("--all", help="Run all", action="store_true")

    args = parser.parse_args()

    assert not all([args.strip, args.annotate]), "Select either --strip or --annotate"
    assert any([args.strip, args.annotate]), "Select either --strip or --annotate"
    if args.all:
        vcf_map = get_vcf_map()
        if args.strip:
            for annotated, unannotated in vcf_map:
                main("strip", annotated, unannotated)
        elif args.annotate:
            for annotated, unannotated in vcf_map:
                main("annotate", unannotated, annotated)
        exit(0)

    assert os.path.isfile(args.f)
    if args.strip:
        main("strip", args.f, args.o)
    elif args.annotate:
        main("annotate", args.f, args.o)
    else:
        raise RuntimeError("Unknown command %s" % args.c)
