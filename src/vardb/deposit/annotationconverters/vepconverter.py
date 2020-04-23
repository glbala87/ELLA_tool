import re
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


class VEPConverter:

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

    def __init__(self, config):
        self.config = config
        self.hgnc_approved_id_symbol, self.hgnc_approved_symbol_id = get_hgnc_approved_symbol_maps()
        self.ncbi_ensembl_hgnc_id = get_hgnc_ncbi_ensembl_map()

    def _get_is_last_exon(self, transcript_data):
        exon = transcript_data.get("exon")
        if exon:
            parts = exon.split("/")
            return parts[0] == parts[1]
        return False

    def _calculate_distances(self, hgvsc):
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
        match = VEPConverter.HGVSC_DISTANCE_CHECK_REGEX.match(hgvsc)
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

    def convert(self, annotation, annotations):

        if self.config["source"] not in annotation:
            return

        # Prefer refseq annotations coming from the latest annotated RefSeq release (RefSeq_gff) over the
        # RefSeq interim release (RefSeq_Interim_gff) and VEP default (RefSeq).
        refseq_priority = ["RefSeq_gff", "RefSeq_Interim_gff", "RefSeq"]

        transcripts = list()
        # Invert CSQ data to map to transcripts
        for data in annotation[self.config["source"]]:
            # Filter out non-transcripts,
            # and only include normal RefSeq or Ensembl transcripts
            if data.get("Feature_type") != "Transcript" or not any(
                data.get("Feature", "").startswith(t) for t in ["NM_", "ENST"]
            ):
                continue

            transcript_data = {k[1]: data[k[0]] for k in VEPConverter.CSQ_FIELDS if k[0] in data}

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

                exon_distance, coding_region_distance = self._calculate_distances(hgvsc)
                transcript_data["exon_distance"] = exon_distance
                transcript_data["coding_region_distance"] = coding_region_distance

            if "HGVSp" in transcript_data:  # Remove transcript part
                transcript_data["protein"], transcript_data["HGVSp"] = transcript_data[
                    "HGVSp"
                ].split(":", 1)

            transcript_data["in_last_exon"] = (
                "yes" if self._get_is_last_exon(transcript_data) else "no"
            )

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
        annotations[self.config["target"]] = transcripts
