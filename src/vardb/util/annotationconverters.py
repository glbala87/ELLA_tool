import re
import json
import base64
import jsonschema
from collections import defaultdict
import gzip
from pathlib import Path
from typing import Any

import logging

log = logging.getLogger(__name__)


def get_hgnc_approved_symbol_maps():
    this_dir = Path(__file__).parent.absolute()
    with gzip.open(this_dir / "hgnc_symbols_id.txt.gz", "rt") as hgnc_symbols:
        hgnc_approved_symbol_id: Any = {}
        hgnc_approved_id_symbol: Any = {}
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
                # This is a previously approved symbol for a HGNC id
                # Discarding this for now, but can be used to map from old symbol
                # to new symbol
                pass

    return hgnc_approved_id_symbol, hgnc_approved_symbol_id


def get_hgnc_ncbi_ensembl_map():
    this_dir = Path(__file__).parent.absolute()
    with gzip.open(this_dir / "hgnc_ncbi_ensembl_geneids.txt.gz", "rt") as hgnc_ncbi_ensembl:
        ncbi_ensembl_hgnc_id: Any = {}
        for l in hgnc_ncbi_ensembl:
            if l.startswith("#"):
                continue
            lsplit = l.strip().split("\t")
            lsplit.extend([""] * (3 - len(lsplit)))  # Make sure line has all three columns
            hgnc_id, ensembl_gene, ncbi_gene = lsplit
            hgnc_id = int(hgnc_id)
            if ensembl_gene != "":
                assert ensembl_gene not in ncbi_ensembl_hgnc_id
                ncbi_ensembl_hgnc_id[ensembl_gene] = hgnc_id
            if ncbi_gene != "":
                assert ncbi_gene not in ncbi_ensembl_hgnc_id
                ncbi_ensembl_hgnc_id[ncbi_gene] = hgnc_id
            assert ensembl_gene == "" or ensembl_gene.startswith("ENSG")
            assert ncbi_gene == "" or int(ncbi_gene)

    return ncbi_ensembl_hgnc_id


class ConvertCSQ(object):
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
        ("SOURCE", "source"),
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

    def __init__(self):
        self.hgnc_approved_id_symbol, self.hgnc_approved_symbol_id = get_hgnc_approved_symbol_maps()
        self.ncbi_ensembl_hgnc_id = get_hgnc_ncbi_ensembl_map()

    def convert_raw(self, raw_csq, csq_header):
        def _parseMAF(val):
            maf = dict()
            alleles = val.split("&")
            for allele in alleles:
                v = allele.split(":")
                for key, value in zip(v[0::2], v[1::2]):
                    try:
                        maf[key] = float(value)
                    except ValueError:
                        continue
            return maf

        converters = {
            "AA_MAF": _parseMAF,
            "AFR_MAF": _parseMAF,
            "AMR_MAF": _parseMAF,
            "ALLELE_NUM": int,
            "ASN_MAF": _parseMAF,
            "EA_MAF": _parseMAF,
            "EUR_MAF": _parseMAF,
            "EAS_MAF": _parseMAF,
            "SAS_MAF": _parseMAF,
            "GMAF": _parseMAF,
            "Consequence": lambda x: [i for i in x.split("&")],
            "Existing_variation": lambda x: [i for i in x.split("&")],
            "DISTANCE": int,
            "STRAND": int,
            "PUBMED": lambda x: [int(i) for i in x.split("&")],
        }

        fields = csq_header["Description"].split("Format: ", 1)[1].split("|")

        transcripts = raw_csq.split(",")

        converted = [
            {k: converters.get(k, lambda x: x)(v) for k, v in zip(fields, t.split("|")) if v != ""}
            for t in transcripts
        ]
        return converted

    def __call__(self, raw_csq, csq_header):
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
            match = ConvertCSQ.HGVSC_DISTANCE_CHECK_REGEX.match(hgvsc)
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
                        "Unable to compute distance from ({}, {}), ({}, {})".format(
                            pm1, d1, pm2, d2
                        )
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

        if raw_csq is None:
            return list()

        assert csq_header, "Unable to parse VEP without INFO header for CSQ"

        csq = self.convert_raw(raw_csq, csq_header)

        # Prefer refseq annotations coming from the latest annotated RefSeq release (RefSeq_gff) over the
        # RefSeq interim release (RefSeq_Interim_gff) and VEP default (RefSeq).
        refseq_priority = ["RefSeq_gff", "RefSeq_Interim_gff", "RefSeq"]

        transcripts = list()
        # Invert CSQ data to map to transcripts
        for data in csq:
            # Filter out non-transcripts,
            # and only include normal RefSeq or Ensembl transcripts
            if data.get("Feature_type") != "Transcript" or not any(
                data.get("Feature", "").startswith(t) for t in ["NM_", "ENST"]
            ):
                continue

            transcript_data = {k[1]: data[k[0]] for k in ConvertCSQ.CSQ_FIELDS if k[0] in data}

            if "hgnc_id" in transcript_data:
                transcript_data["hgnc_id"] = int(transcript_data["hgnc_id"])
            elif "Gene" in data and data["Gene"] in self.ncbi_ensembl_hgnc_id:
                transcript_data["hgnc_id"] = self.ncbi_ensembl_hgnc_id[data["Gene"]]
            elif "SYMBOL" in data and data["SYMBOL"] in self.hgnc_approved_symbol_id:
                transcript_data["hgnc_id"] = self.hgnc_approved_symbol_id[data["SYMBOL"]]
            else:
                if data.get("SYMBOL_SOURCE") not in [
                    "Clone_based_vega_gene",
                    "Clone_based_ensembl_gene",
                ]:  # Silently ignore these sources, to avoid cluttering the log
                    log.warning(
                        "No HGNC id found for Feature: {}, SYMBOL: {}, SYMBOL_SOURCE: {}, Gene: {}. Skipping.".format(
                            data.get("Feature", "N/A"),
                            data.get("SYMBOL", "N/A"),
                            data.get("SYMBOL_SOURCE", "N/A"),
                            data.get("Gene", "N/A"),
                        )
                    )
                continue
            assert "hgnc_id" in transcript_data and isinstance(
                transcript_data["hgnc_id"], int
            ), str(data)

            if "symbol" not in transcript_data:
                transcript_data["symbol"] = self.hgnc_approved_id_symbol[transcript_data["hgnc_id"]]

            # Only keep dbSNP data (e.g. rs123456789)
            if "dbsnp" in transcript_data:
                transcript_data["dbsnp"] = [
                    t for t in transcript_data["dbsnp"] if t.startswith("rs")
                ]

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
                transcript_data["protein"], transcript_data["HGVSp"] = transcript_data[
                    "HGVSp"
                ].split(":", 1)

            transcript_data["in_last_exon"] = "yes" if _get_is_last_exon(transcript_data) else "no"

            # All lists must be deterministic
            if "consequences" in transcript_data:
                transcript_data["consequences"] = sorted(transcript_data["consequences"])
            else:
                transcript_data["consequences"] = []

            # Check if this transcript is already processed, and if so, check if this should be overwritten
            # by incoming transcript_data based on refseq_priority. We do not want multiple annotations
            # on the same transcript. Chances are that the annotations (HGVSc, HGVSp, consequences) are equal,
            # but in a small percentage of cases the different sources can give different annotations.
            existing_tx_data = next(
                (
                    tx_data
                    for tx_data in transcripts
                    if tx_data["transcript"] == transcript_data["transcript"]
                ),
                None,
            )

            if existing_tx_data:
                assert (
                    "source" in existing_tx_data and "source" in transcript_data
                ), "Unable to determine priority of transcript {}, as source is not defined".format(
                    transcript_data["transcript"]
                )

                existing_source = existing_tx_data["source"]
                incoming_source = transcript_data["source"]
                assert (
                    existing_source in refseq_priority and incoming_source in refseq_priority
                ), "Transcript {} defined multiple times in annotation, but no priority defined for the sources {} and {}".format(
                    transcript_data["transcript"], existing_source, incoming_source
                )

                if refseq_priority.index(existing_source) > refseq_priority.index(incoming_source):
                    # Incoming has priority, replace existing
                    transcripts[transcripts.index(existing_tx_data)] = transcript_data
                else:
                    # Existing has priority, discard incoming
                    continue
            else:
                transcripts.append(transcript_data)

        # Remove no longer needed source
        [tx.pop("source") for tx in transcripts if "source" in tx]

        # VEP output is not deterministic, but we need it to be so
        # we can compare correctly in database
        transcripts = sorted(transcripts, key=lambda x: x["transcript"])

        return transcripts


_HGMD_SUBSTITUTE = [
    (re.compile(r"@#EQ"), "="),
    (re.compile(r"@#CM"), ","),
    (re.compile(r"@#SC"), ";"),
    (re.compile(r"@#SP"), " "),
    (re.compile(r"@#TA"), "\t"),
]


def _translate_to_original(x):
    if not isinstance(x, str):
        return x
    for regexp, substitution in _HGMD_SUBSTITUTE:
        x = regexp.sub(substitution, x)
    return x


def convert_hgmd(annotation):
    if not any(x.startswith("HGMD") for x in annotation):
        return dict()
    HGMD_FIELDS = ["HGMD__acc_num", "HGMD__codon", "HGMD__disease", "HGMD__tag"]

    data = {
        k.split("__")[-1]: _translate_to_original(annotation[k])
        for k in HGMD_FIELDS
        if k in annotation
    }
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
    for full_key, value in annotation.items():
        if not full_key.startswith(annotation_key):
            continue
        else:
            key = full_key.split(annotation_key + "__")[-1]

        if value == ["."] or value == ".":
            continue
        if key == "AS_FilterStatus":  # gnomAD specific
            filter_status = {"G": value.split("|")}
        elif key.startswith("filter_"):
            pop = key.split("filter_")[1]
            filter_status[pop] = re.split(r",|\|", value)
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


def gnomad_exomes_frequencies(annotation):
    """
    Manually calculate frequencies from raw GNOMAD Exomoes data.

    :param: annotation: a dict with key 'GNOMAD_EXOMES'
    :returns: dict with key 'GNOMAD_EXOMES'
    """
    return extract_annotation_frequencies(annotation, "GNOMAD_EXOMES", "GNOMAD_EXOMES")


def gnomad_genomes_frequencies(annotation):
    """
    Manually calculate frequencies from raw Gnomad Genomes data.

    :param: annotation: a dict with key 'GNOMAD_GENOMES'
    :returns: dict with key 'GNOMAD_GENOMES'
    """

    return extract_annotation_frequencies(annotation, "GNOMAD_GENOMES", "GNOMAD_GENOMES")


def indb_frequencies(annotation):
    """
    Manually calculate frequencies from raw Gnomad Genomes data.

    :param: annotation: a dict with key 'GNOMAD_GENOMES'
    :returns: dict with key 'GNOMAD_GENOMES'
    """

    return extract_annotation_frequencies(annotation, "inDB", "inDB")


class ConvertReferences(object):

    REFTAG = {
        "APR": "Additional phenotype",
        "FCR": "Functional characterisation",
        "MCR": "Molecular characterisation",
        "SAR": "Additional report",
    }

    def _hgmd_pubmeds(self, annotation, meta):
        total = dict()

        if "HGMD__pmid" in annotation:
            pmid = annotation["HGMD__pmid"]
            reftag = "Primary literature report"
            comments = annotation.get("HGMD__comments", "No comments")
            comments = "No comments." if comments == "None" else comments
            total[pmid] = [reftag, _translate_to_original(comments)]

        if "HGMD__extrarefs" in annotation:
            header_extrarefs = next(
                (x for x in meta.get("INFO", []) if x["ID"] == "HGMD__extrarefs"), None
            )
            assert (
                header_extrarefs is not None
            ), "Header for HGMD__extrarefs is not defined. Unable to parse HGMD__extrarefs"
            extraref_keys = re.findall(r"Format: \((.*?)\)", header_extrarefs["Description"])[
                0
            ].split("|")
            for er in annotation["HGMD__extrarefs"].split(","):
                er_data = dict(zip(extraref_keys, er.split("|")))
                pmid = er_data["pmid"]
                reftag = ConvertReferences.REFTAG.get(er_data.get("reftag"), "Reftag not specified")
                comments = er_data.get("comments", "No comments.")
                comments = "No comments." if not comments else comments

                # The comment on APR is the disease/phenotype
                if er_data.get("reftag") == "APR" and comments == "No comments.":
                    comments = er_data.get("disease", comments)

                total[pmid] = [reftag, _translate_to_original(comments)]

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
        pubmeds += clinvarjson.get("pubmed_ids", [])
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

    def process(self, annotation, meta):
        hgmd_pubmeds = self._ensure_int_pmids(self._hgmd_pubmeds(annotation, meta))
        references = [
            {"pubmed_id": pmid, "source": "HGMD", "source_info": info_string}
            for pmid, info_string in hgmd_pubmeds.items()
        ]
        clinvar_pubmeds = self._ensure_int_pmids(self._clinvar_pubmeds(annotation))
        references += [
            {"pubmed_id": pmid, "source": "CLINVAR", "source_info": info_string}
            for pmid, info_string in clinvar_pubmeds.items()
        ]

        return references
