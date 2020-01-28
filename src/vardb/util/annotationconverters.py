import re
import json
import base64
import jsonschema
from collections import defaultdict

import logging

log = logging.getLogger(__name__)

# the annotation key is found in the VCF
# the result key is put in our annotation database
EXAC_ANNOTATION_KEY = "EXAC"
EXAC_RESULT_KEY = "ExAC"

GNOMAD_EXOMES_ANNOTATION_KEY = "GNOMAD_EXOMES"
GNOMAD_EXOMES_RESULT_KEY = "GNOMAD_EXOMES"

GNOMAD_GENOMES_ANNOTATION_KEY = "GNOMAD_GENOMES"
GNOMAD_GENOMES_RESULT_KEY = "GNOMAD_GENOMES"

INDB_ANNOTATION_KEY = "inDB"
INDB_RESULT_KEY = "inDB"

SPLICE_FIELDS = [
    ("Effect", "effect"),
    ("Transcript", "transcript"),
    ("MaxEntScan-mut", "maxentscan_mut"),
    ("MaxEntScan-wild", "maxentscan_wild"),
    ("MaxEntScan-closest", "maxentscan_closest"),  # relevant for 'de novo'
    ("dist", "dist"),  # relevant for 'de novo'
]


CSQ_FIELDS = [
    # (source, dest) key names
    ("Consequence", "consequences"),
    ("HGNC_ID", "hgnc_id"),
    ("SYMBOL", "symbol"),
    ("HGVSc", "HGVSc"),
    ("HGVSp", "HGVSp"),
    ("STRAND", "strand"),
    ("Amino_acids", "amino_acids"),
    ("Existing_variation", "dbsnp"),
    ("EXON", "exon"),
    ("INTRON", "intron"),
    ("Codons", "codons"),
    ("Feature", "transcript"),
    ("CANONICAL", "is_canonical"),
]

# Should match all possible valid HGVSc annotations (without transcript)
# We use the resulting regex groups below in _calculate_distances, to compute distance
# from coding start (for exonic UTR variants), and exon distance (for intronic variants)
# Examples of valid HGVSc:
# c.279G>A
# n.1901_1904delAAGT
# c.248-1_248insA
# c.11712-20dupT
# c.1624+24T>A
# c.*14G>A
# c.-315_-314delAC

HGVSC_DISTANCE_CHECK = [
    r"(?P<c>[cn])\.",  # Coding or non-coding
    r"(?P<utr1>[\*\-]?)",  # UTR direction (asterisk is 5' UTR, minus is 3' UTR),
    r"(?P<p1>[0-9]+)",  # Position (distance into UTR if UTR region)
    r"(?P<pm1>[\-\+]?)",  # Intron direction if variant is intronic
    r"(?P<ed1>([0-9]+)?)",  # Distance from intron if variant is intronic
    r"((?P<region>_)",  # If del/dup/ins, we could have a region, denoted by a '_'. What follows below is only applicable to those cases
    r"(?P<utr2>[\*\-]?)",
    r"(?P<p2>[0-9]+)",
    r"(?P<pm2>[\-\+]?)",
    r"(?P<ed2>([0-9]+)?)",
    r")?",  # End of region
    r"([ACGT]|[BDHKMNRSVWY]|del|dup|ins|inv)",  # All possible options following the position
]
HGVSC_DISTANCE_CHECK_REGEX = re.compile("".join(HGVSC_DISTANCE_CHECK))

import gzip
from pathlib import Path

this_dir = Path(__file__).parent.absolute()
with gzip.open(this_dir / "hgnc_symbols_id.txt.gz", "rt") as hgnc_symbols:
    hgnc_approved_symbol_id = {}
    hgnc_previous_symbol_id = {}
    hgnc_approved_id_symbol = {}
    # hgnc_previous_id_symbol = {}
    for l in hgnc_symbols:
        if l.startswith("#"):
            continue
        symbol, hgnc_id, approved = l.strip().split("\t")
        hgnc_id = int(hgnc_id)
        if approved == "1":
            assert symbol not in hgnc_approved_symbol_id
            assert hgnc_id not in hgnc_approved_id_symbol
            hgnc_approved_symbol_id[symbol] = hgnc_id
            hgnc_approved_id_symbol[hgnc_id] = symbol
        else:
            assert symbol not in hgnc_previous_symbol_id
            # assert hgnc_id not in hgnc_previous_id_symbol
            hgnc_previous_symbol_id[symbol] = hgnc_id
            # hgnc_previous_id_symbol[hgnc_id] = symbol

with gzip.open(this_dir / "hgnc_ncbi_ensembl_geneids.txt.gz", "rt") as hgnc_ncbi_ensembl:
    ncbi_ensembl_hgnc_id = {}
    for l in hgnc_ncbi_ensembl:
        if l.startswith("#"):
            continue
        lsplit = l.strip().split("\t")
        lsplit = lsplit + [""] * (3 - len(lsplit))
        # print(len(lsplit), lsplit)
        hgnc_id, ensembl_gene, ncbi_gene = lsplit
        hgnc_id = int(hgnc_id)
        if ensembl_gene:
            assert ensembl_gene not in ncbi_ensembl_hgnc_id
            ncbi_ensembl_hgnc_id[ensembl_gene] = hgnc_id
        if ncbi_gene:
            assert ncbi_gene not in ncbi_ensembl_hgnc_id
            ncbi_ensembl_hgnc_id[ncbi_gene] = hgnc_id
        # print(ensembl_gene)
        assert ensembl_gene == "" or ensembl_gene.startswith("ENSG")
        assert ncbi_gene == "" or int(ncbi_gene)
        # print(hgnc_id, ensembl_gene, ncbi_gene)
# exit()


def _map_hgnc_id(transcripts):
    symbol_hgnc_id = dict()
    for t in transcripts:
        if t.get("hgnc_id") and isinstance(t.get("hgnc_id"), int):
            if t["symbol"] in symbol_hgnc_id:
                assert (
                    symbol_hgnc_id[t["symbol"]] == t["hgnc_id"]
                ), "Got different HGNC ({} vs {}) id for same gene symbol ({})".format(
                    t["hgnc_id"], symbol_hgnc_id[t["symbol"]], t["symbol"]
                )
            symbol_hgnc_id[t["symbol"]] = t["hgnc_id"]
    return symbol_hgnc_id


def _map_hgnc_id_gene(transcripts):
    gene_hgnc_id = dict()
    for t in transcripts:
        if t.get("hgnc_id") and isinstance(t.get("hgnc_id"), int):
            if t["gene"] in gene_hgnc_id:
                assert (
                    gene_hgnc_id[t["symbol"]] == t["hgnc_id"]
                ), "Got different HGNC ({} vs {}) id for same gene symbol ({})".format(
                    t["hgnc_id"], gene_hgnc_id[t["symbol"]], t["symbol"]
                )
            gene_hgnc_id[t["symbol"]] = t["hgnc_id"]
    return gene_hgnc_id


def convert_csq(annotation):
    def _get_is_last_exon(transcript_data):
        exon = transcript_data.get("exon")
        if exon:
            parts = exon.split("/")
            return parts[0] == parts[1]
        return False

    def _calculate_distances(hgvsc):
        """Calculate distances from valid HGVSc.
        References:
        Numbering: http://varnomen.hgvs.org/bg-material/numbering/
        Naming: http://varnomen.hgvs.org/bg-material/standards/

        exon_distance denotes distance from exon for intron variants. For exonic variants, this is 0.

        coding_region_distance denotes distance from coding region of the *spliced* gene.
        This only applies to exonic variants. Used for determining distance into UTR-region of a variant.

        Returns (exon_distance, utr_distance)

        Examples:
                hgvsc        | exon_distance | coding_region_distance
        --------------------+---------------+------------------------
          c.279G>A           |             0 |                      0
          n.1901_1904delAAGT |             0 |                      0
          c.248-1_248insA    |             0 |                      0
          c.11712-20dupT     |           -20 |
          c.1624+24T>A       |            24 |
          c.*14G>A           |             0 |                     14
          c.-315_-314delAC   |             0 |                   -314
        """
        match = HGVSC_DISTANCE_CHECK_REGEX.match(hgvsc)
        if not match:
            if hgvsc:
                log.warning("Unable to parse distances from hgvsc: {}".format(hgvsc))
            return None, None

        exon_distance = None
        coding_region_distance = None
        match_data = match.groupdict()

        # Region variants could extend from intron into an exon, e.g. c.*431-1_*431insA
        # The regex would then match on ed1, but not on ed2 (and return distance of -1)
        # However, if it matches on one of them, but not the other, we force the other to be "0"
        def fix_region_distance(d1, d2):
            if d1 or d2:
                d1 = d1 if d1 else "0"
                d2 = d2 if d2 else "0"
                return d1, d2
            else:
                return d1, d2

        if match_data["region"]:
            match_data["ed1"], match_data["ed2"] = fix_region_distance(
                match_data["ed1"], match_data["ed2"]
            )

        def get_distance(pm1, d1, pm2, d2):
            if not (pm1 or pm2):
                # If neither pm1 or pm2 is provided, we are at an exonic variant
                return 0
            elif d1 and not d2:
                # Happens for simple snips, e.g c.123-46A>G or c.*123A>G
                assert not pm2
                return -int(d1) if pm1 == "-" else int(d1)
            elif d1 and d2:
                # Take the minimum of the two, as this is closest position to the exon/coding start
                d = min(int(d1), int(d2))
                if int(d1) == d:
                    return -d if pm1 == "-" else d
                else:
                    return -d if pm2 == "-" else d
            else:
                raise RuntimeError(
                    "Unable to compute distance from ({}, {}), ({}, {})".format(pm1, d1, pm2, d2)
                )

        exon_distance = get_distance(
            match_data["pm1"], match_data["ed1"], match_data["pm2"], match_data["ed2"]
        )

        if exon_distance == 0:
            if (match_data["p1"] and not match_data["utr1"]) or (
                match_data["p2"] and not match_data["utr2"]
            ):
                # Since utr1/utr2 is always shown as either * or - for UTR regions, we know that we are in a coding region
                # if either of those are empty
                coding_region_distance = 0
            else:
                coding_region_distance = get_distance(
                    match_data["utr1"], match_data["p1"], match_data["utr2"], match_data["p2"]
                )

        return exon_distance, coding_region_distance

    if "CSQ" not in annotation:
        return list()

    transcripts = list()
    # Invert CSQ data to map to transcripts
    for data in annotation["CSQ"]:
        # Filter out non-transcripts,
        # and only include normal RefSeq or Ensembl transcripts
        if data.get("Feature_type") != "Transcript" or not any(
            data.get("Feature", "").startswith(t) for t in ["NM_", "ENST"]
        ):
            continue

        transcript_data = {k[1]: data[k[0]] for k in CSQ_FIELDS if k[0] in data}

        if "hgnc_id" in transcript_data:
            transcript_data["hgnc_id"] = int(transcript_data["hgnc_id"])
        elif "Gene" in data and data["Gene"] in ncbi_ensembl_hgnc_id:
            transcript_data["hgnc_id"] = ncbi_ensembl_hgnc_id[data["Gene"]]
        elif "SYMBOL" in data and data["SYMBOL"] in hgnc_approved_symbol_id:
            transcript_data["hgnc_id"] = hgnc_approved_symbol_id[data["SYMBOL"]]
        else:
            if data.get("SYMBOL_SOURCE") not in [
                "Clone_based_vega_gene",
                "Clone_based_ensembl_gene",
            ]:
                log.warning(
                    "No HGNC id found for Feature: {}, SYMBOL: {}, SYMBOL_SOURCE: {}, Gene: {}. Skipping.".format(
                        data.get("Feature", "N/A"),
                        data.get("SYMBOL", "N/A"),
                        data.get("SYMBOL_SOURCE", "N/A"),
                        data.get("Gene", "N/A"),
                    )
                )
            continue
        assert "hgnc_id" in transcript_data and isinstance(transcript_data["hgnc_id"], int), str(
            data
        )

        if "symbol" not in transcript_data:
            transcript_data["symbol"] = hgnc_approved_id_symbol[transcript_data["hgnc_id"]]

        if data.get("SYMBOL_SOURCE") == "RFAM":
            print(transcript_data["hgnc_id"])

        # Only keep dbSNP data (e.g. rs123456789)
        if "dbsnp" in transcript_data:
            transcript_data["dbsnp"] = [t for t in transcript_data["dbsnp"] if t.startswith("rs")]

        # Convert 'is_canonical' to bool
        transcript_data["is_canonical"] = transcript_data.get("is_canonical") == "YES"

        # Add custom types
        if "HGVSc" in transcript_data:

            transcript_name, hgvsc = transcript_data["HGVSc"].split(":", 1)
            transcript_data["HGVSc"] = hgvsc  # Remove transcript part

            # Split away transcript part and remove long (>10 nt) insertions/deletions/duplications
            def repl_len(m):
                return "(" + str(len(m.group())) + ")"

            s = re.sub("(?<=ins)([ACGT]{10,})", repl_len, hgvsc)
            insertion = re.search("(?<=ins)([ACGT]{10,})", hgvsc)
            if insertion is not None:
                transcript_data["HGVSc_insertion"] = insertion.group()
            s = re.sub("(?<=[del|dup])[ACGT]{10,}", "", s)
            transcript_data["HGVSc_short"] = s

            exon_distance, coding_region_distance = _calculate_distances(hgvsc)
            transcript_data["exon_distance"] = exon_distance
            transcript_data["coding_region_distance"] = coding_region_distance

        if "HGVSp" in transcript_data:  # Remove transcript part
            transcript_data["protein"], transcript_data["HGVSp"] = transcript_data["HGVSp"].split(
                ":", 1
            )

        transcript_data["in_last_exon"] = "yes" if _get_is_last_exon(transcript_data) else "no"

        # All lists must be deterministic
        if "consequences" in transcript_data:
            transcript_data["consequences"] = sorted(transcript_data["consequences"])
        else:
            transcript_data["consequences"] = []
        transcripts.append(transcript_data)

    # VEP output is not deterministic, but we need it to be so
    # we can compare correctly in database
    transcripts = sorted(transcripts, key=lambda x: x["transcript"])

    # Hack: Since hgnc_id is not provided by VEP for Refseq,
    # we steal it from matching Ensembl transcript (by gene symbol)
    # Tested on 100k exome annotated variants, all RefSeq had corresponding match in Ensembl
    symbol_hgnc_id = _map_hgnc_id(transcripts)
    # for t in transcripts:
    #     if not t.get("hgnc_id") and t.get("symbol") and t["symbol"] in symbol_hgnc_id:
    #         t["hgnc_id"] = symbol_hgnc_id[t["symbol"]]
    #     elif not t.get("hgnc_id") and t.get("symbol"):
    #         t["hgnc_id"] = hgnc_approved_symbol_id.get(
    #             t["symbol"], hgnc_previous_symbol_id.get(t["symbol"])
    #         )
    #     if not t.get("hgnc_id"):
    #         import json

    #         if t["transcript"].startswith("NM"):

    #             print(json.dumps(annotation["CSQ"], indent=2))
    #             print(t)
    #         continue

    #     if t.get("symbol"):
    #         if not (t.get("hgnc_id") and t["hgnc_id"]):
    #             log.warning("Missing HGNC ID for gene symbol {}".format(t["symbol"]))

    #         vep_hgnc_id = t["hgnc_id"]
    #         hgnc_id = hgnc_approved_symbol_id.get(
    #             t["symbol"], hgnc_previous_symbol_id.get(t["symbol"])
    #         )
    #         assert (
    #             hgnc_id is None or hgnc_id == vep_hgnc_id
    #         ), "Mismatch between VEP provided HGNC id ({}) and HGNC provided id ({}) for symbol {}".format(
    #             vep_hgnc_id, hgnc_id, t["symbol"]
    #         )

    #         if t["symbol"] not in hgnc_approved_symbol_id:
    #             # Not approved symbol
    #             if t["hgnc_id"] not in hgnc_approved_id_symbol:
    #                 log.warning("HGNC ID {} has no approved symbol".format(t["hgnc_id"]))
    #             else:
    #                 approved_symbol = hgnc_approved_id_symbol[t["hgnc_id"]]
    #                 log.warning(
    #                     "VEP provided symbol {} for HGNC ID {}, approved symbol is {}".format(
    #                         t["symbol"], t["hgnc_id"], approved_symbol
    #                     )
    #                 )

    return transcripts


HGMD_FIELDS = ["acc_num", "codon", "disease", "tag"]


def convert_hgmd(annotation):
    if "HGMD" not in annotation:
        return dict()

    data = {k: annotation["HGMD"][k] for k in HGMD_FIELDS if k in annotation["HGMD"]}
    return {"HGMD": data}


# Schema for checking incoming CLINVAR data (not the data ending up in the database)
CLINVAR_V1_INCOMING_SCHEMA = {
    "definitions": {
        "rcv": {
            "$id": "#/definitions/rcv",
            "type": "object",
            "required": [
                "traitnames",
                "clinical_significance_descr",
                "variant_id",
                "submitter",
                "last_evaluated",
            ],
            "properties": {
                "traitnames": {"type": "array", "items": {"type": "string"}},
                "clinical_significance_descr": {"type": "array", "items": {"type": "string"}},
                "variant_id": {"type": "array", "items": {"type": "string"}},
                "submitter": {"type": "array", "items": {"type": "string"}},
            },
        }
    },
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://example.com/root.json",
    "type": "object",
    "required": ["variant_description", "variant_id", "rcvs"],
    "properties": {
        "variant_description": {"$id": "#/properties/variant_description", "type": "string"},
        "variant_id": {"$id": "#/properties/variant_id", "type": "integer"},
        "rcvs": {"type": "object", "patternProperties": {"": {"$ref": "#/definitions/rcv"}}},
    },
}


def _convert_clinvar_v1(clinvarjson):
    CLINVAR_FIELDS = ["variant_description", "variant_id"]
    CLINVAR_RCV_FIELDS = [
        "traitnames",
        "clinical_significance_descr",
        "variant_id",
        "submitter",
        "last_evaluated",
    ]
    data = dict(items=[])
    data.update({k: clinvarjson[k] for k in CLINVAR_FIELDS})

    for rcv, val in list(clinvarjson["rcvs"].items()):
        item = {k: ", ".join(val[k]) for k in CLINVAR_RCV_FIELDS}
        item["rcv"] = rcv
        data["items"].append(item)

    return data


def convert_clinvar(annotation):
    if "CLINVARJSON" not in annotation:
        return dict()

    clinvarjson = json.loads(
        base64.b16decode(annotation["CLINVARJSON"]).decode(encoding="utf-8", errors="strict")
    )
    # Legacy: In version 1 of the ClinVar data, we performed additional parsing of the clinvar data.
    # The validation of the resulting clinvar json is done in the database.
    try:
        jsonschema.validate(clinvarjson, CLINVAR_V1_INCOMING_SCHEMA)
        return {"CLINVAR": _convert_clinvar_v1(clinvarjson)}
    except jsonschema.ValidationError:
        return {"CLINVAR": clinvarjson}


def extract_annotation_frequencies(annotation, annotation_key, result_key):
    frequencies = defaultdict(dict)

    # TODO: Remove when annotation isn't so messed up...
    def extract_int_list(value):
        if isinstance(value, list):
            assert len(value) == 1
            value = value[0]
        value = int(value)
        return value

    freq = {}
    count = {}
    num = {}
    hom = {}
    hemi = {}
    filter_status = {}
    indications = {}
    for key, value in annotation[annotation_key].items():
        if value == ["."] or value == ".":
            continue
        if key == "AS_FilterStatus":  # gnomAD specific
            assert len(value) == 1
            filter_status = {"G": value[0].split("|")}
        elif key.startswith("filter_"):
            pop = key.split("filter_")[1]
            filter_status[pop] = re.split(",|\|", value)
        # Be careful if rearranging!
        elif key == "AC":
            count["G"] = extract_int_list(value)
        elif key in ["AC_Hom", "Hom"]:
            hom["G"] = extract_int_list(value)
        elif key in ["AC_Hemi", "Hemi"]:
            hemi["G"] = extract_int_list(value)
        elif key == "AN":
            num["G"] = value
        elif key.startswith("AC_"):
            pop = key.split("AC_")[1]
            count[pop] = extract_int_list(value)
        elif key.startswith("AN_"):
            pop = key.split("AN_")[1]
            num[pop] = extract_int_list(value)
        elif key.startswith("Hom_"):
            pop = key.split("Hom_")[1]
            hom[pop] = extract_int_list(value)
        elif key.startswith("Hemi_"):
            pop = key.split("Hemi_")[1]
            hemi[pop] = extract_int_list(value)
        elif key.startswith("indications_"):
            pop = key.split("indications_")[1]
            # foo:x,bar:y -> {foo: x, bar:y}
            indications[pop] = {f.split(":", 1)[0]: f.split(":", 1)[1] for f in value.split(",")}

    for key in count:
        if key in num and num[key]:
            freq[key] = float(count[key]) / num[key]

    # ExAC override. ExAC naming is very misleading!
    # ExAC should use Adj, NOT the default AC and AN!
    if result_key == EXAC_RESULT_KEY:
        for item in [count, num, freq]:
            if "Adj" in item:
                item["G"] = item["Adj"]
                del item["Adj"]

    if freq:
        frequencies[result_key].update({"freq": freq})
    if hom:
        frequencies[result_key].update({"hom": hom})
    if hemi:
        frequencies[result_key].update({"hemi": hemi})
    if num:
        frequencies[result_key].update({"num": num})
    if count:
        frequencies[result_key].update({"count": count})
    if filter_status:
        frequencies[result_key].update({"filter": filter_status})
    if indications:
        frequencies[result_key].update({"indications": indications})

    return dict(frequencies)


def exac_frequencies(annotation):
    """
    Manually calculate frequencies from raw ExAC data.

    :param: annotation: a dict with key 'EXAC'
    :returns: dict with key 'ExAC'
    """

    if EXAC_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_frequencies(annotation, EXAC_ANNOTATION_KEY, EXAC_RESULT_KEY)


def gnomad_exomes_frequencies(annotation):
    """
    Manually calculate frequencies from raw GNOMAD Exomoes data.

    :param: annotation: a dict with key 'GNOMAD_EXOMES'
    :returns: dict with key 'GNOMAD_EXOMES'
    """

    if GNOMAD_EXOMES_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_frequencies(
            annotation, GNOMAD_EXOMES_ANNOTATION_KEY, GNOMAD_EXOMES_RESULT_KEY
        )


def gnomad_genomes_frequencies(annotation):
    """
    Manually calculate frequencies from raw Gnomad Genomes data.

    :param: annotation: a dict with key 'GNOMAD_GENOMES'
    :returns: dict with key 'GNOMAD_GENOMES'
    """

    if GNOMAD_GENOMES_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_frequencies(
            annotation, GNOMAD_GENOMES_ANNOTATION_KEY, GNOMAD_GENOMES_RESULT_KEY
        )


def indb_frequencies(annotation):
    """
    Manually calculate frequencies from raw Gnomad Genomes data.

    :param: annotation: a dict with key 'GNOMAD_GENOMES'
    :returns: dict with key 'GNOMAD_GENOMES'
    """
    if INDB_ANNOTATION_KEY not in annotation:
        return {}
    else:
        return extract_annotation_frequencies(annotation, INDB_ANNOTATION_KEY, INDB_RESULT_KEY)


def csq_frequencies(annotation):
    if "CSQ" not in annotation:
        return {}

    # Get first elem which has frequency data (it's the same in all elements)
    frequencies = dict()
    freq_data = next((d for d in annotation["CSQ"] if any("MAF" in k for k in d)), None)
    if freq_data:
        # Check whether the allele provided for the frequency is the same as the one we have in our allele.
        # VEP gives minor allele for some fields, which can be the reference instead of the allele
        processed = {
            k.replace("_MAF", "").replace("MAF", ""): v[freq_data["Allele"]]
            for k, v in freq_data.items()
            if "MAF" in k and freq_data["Allele"] in v
        }
        if processed:
            # ESP6500 freqs
            esp6500_freq = dict()
            for f in ["AA", "EA"]:
                if f in processed:
                    esp6500_freq[f] = processed.pop(f)
            if esp6500_freq:
                frequencies["esp6500"] = {"freq": esp6500_freq}

            if processed:
                frequencies["1000g"] = {"freq": processed}

    return dict(frequencies)


class ConvertReferences(object):

    REFTAG = {
        "APR": "Additional phenotype",
        "FCR": "Functional characterisation",
        "MCR": "Molecular characterisation",
        "SAR": "Additional report",
    }

    def _hgmd_pubmeds(self, annotation):
        if "HGMD" not in annotation:
            return dict()
        total = dict()

        if "pmid" in annotation["HGMD"]:
            pmid = annotation["HGMD"]["pmid"]
            reftag = "Primary literature report"
            comments = annotation["HGMD"].get("comments", "No comments")
            comments = "No comments." if comments == "None" else comments
            total[pmid] = [reftag, comments]

        for er in annotation["HGMD"].get("extrarefs", []):
            if "pmid" in er:

                pmid = er["pmid"]
                reftag = ConvertReferences.REFTAG.get(er.get("reftag"), "Reftag not specified")
                comments = er.get("comments", "No comments.")
                comments = "No comments." if comments == "None" else comments

                # The comment on APR is the disease/phenotype
                if er.get("reftag") == "APR" and comments == "No comments.":
                    comments = er.get("disease", comments)

                total[pmid] = [reftag, comments]

        # Format reftag, comments to string
        for pmid, info in list(total.items()):
            info_string = ". ".join([v.strip().strip(".") for v in info]) + "."
            total[pmid] = info_string

        return total

    def _clinvar_pubmeds(self, annotation):
        if "CLINVARJSON" not in annotation:
            return dict()

        clinvarjson = json.loads(
            base64.b16decode(annotation["CLINVARJSON"]).decode(encoding="utf-8", errors="strict")
        )

        pubmeds = clinvarjson.get("pubmeds", [])
        pubmeds = dict(list(zip(pubmeds, [""] * len(pubmeds))))  # Return as dict (empty values)

        return pubmeds

    def _ensure_int_pmids(self, pmids):
        # HACK: Convert all ids to int, the annotation is sometimes messed up
        # If it cannot be converted, ignore it...
        assert isinstance(pmids, dict)
        int_pmids = dict()
        for pmid, val in pmids.items():
            try:
                int_pmids[int(pmid)] = val
            except ValueError:
                log.warning("Cannot convert pubmed id from annotation to integer: {}".format(val))

        return int_pmids

    def process(self, annotation):
        hgmd_pubmeds = self._ensure_int_pmids(self._hgmd_pubmeds(annotation))
        clinvar_pubmeds = self._ensure_int_pmids(self._clinvar_pubmeds(annotation))

        # Merge references and restructure to list
        all_pubmeds = list(hgmd_pubmeds.keys()) + list(clinvar_pubmeds.keys())
        references = list()
        for pmid in sorted(set(all_pubmeds), key=all_pubmeds.count, reverse=True):
            sources = []
            sourceInfo = dict()
            if pmid in hgmd_pubmeds:
                sources.append("HGMD")
                if hgmd_pubmeds[pmid] != "":
                    sourceInfo["HGMD"] = hgmd_pubmeds[pmid]
            if pmid in clinvar_pubmeds:
                sources.append("CLINVAR")
                if clinvar_pubmeds[pmid] != "":
                    sourceInfo["CLINVAR"] = clinvar_pubmeds[pmid]

            references.append({"pubmed_id": pmid, "sources": sources, "source_info": sourceInfo})

        return references
