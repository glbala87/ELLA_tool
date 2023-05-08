import gzip
import logging
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from typing_extensions import Literal
from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
)

log = logging.getLogger(__name__)
YesNo = Union[Literal["yes"], Literal["no"]]


@dataclass(init=False)
class TranscriptData:
    """
    Transcript annotation object, see jsonschemas/annotation/transcripts_v1.json for additional
    details. No validation is done until checked against the schema on database insert.
    """

    consequences: List[str]
    hgnc_id: int
    symbol: str
    HGVSc: Optional[str]
    HGVSc_short: Optional[str]
    HGVSc_insertion: Optional[str]
    HGVSp: Optional[str]
    protein: Optional[str]
    strand: int
    amino_acids: Optional[str]
    dbsnp: Optional[List[str]]
    exon: Optional[str]
    intron: Optional[str]
    codons: Optional[str]
    transcript: str
    is_canonical: bool
    exon_distance: Optional[int]
    coding_region_distance: Optional[int]
    in_last_exon: YesNo
    splice: Optional[List]
    _source: Optional[str]

    # dataclass doesn't do any validation anyway, so just set optional fields to None
    # and then set other fields as the data is processed
    def __init__(self, full_tx_data: Mapping[str, str]) -> None:
        self._source = None
        self.amino_acids = None
        self.exon = None
        self.intron = None
        self.codons = None
        self.dbsnp = None
        self.HGVSc = None
        self.HGVSc_insertion = None
        self.HGVSc_short = None
        self.exon_distance = None
        self.coding_region_distance = None
        self.protein = None
        self.HGVSp = None
        self.splice = None
        self._mandatory_fields = (
            "transcript",
            "strand",
            "is_canonical",
            "in_last_exon",
            "consequences",
            "hgnc_id",
            "source",
            "symbol",
            "exon_distance",
            "coding_region_distance",
        )
        self._full_tx_data = full_tx_data

        self._setup()
        self._process_data()

    def _setup(self) -> None:
        (
            self._hgnc_approved_id_symbol,
            self._hgnc_approved_symbol_id,
        ) = get_hgnc_approved_symbol_maps()
        self._ncbi_ensembl_hgnc_id = get_hgnc_ncbi_ensembl_map()

    def _process_data(self) -> None:
        self._required_no_conversion()
        self._convert_required()
        self._optional_no_conversion()
        self._convert_optional()

    def _required_no_conversion(self) -> None:
        "Required fields that does not require conversion"
        self.transcript = self._full_tx_data["Feature"]
        self._source = self._full_tx_data.get("SOURCE")

    def _optional_no_conversion(self) -> None:
        "Optional fields that does not require conversion"
        optional_fields = {
            "Amino_acids": "amino_acids",
            "EXON": "exon",
            "INTRON": "intron",
            "Codons": "codons",
        }
        for key, target in optional_fields.items():
            if self._full_tx_data.get(key):
                setattr(self, target, self._full_tx_data[key])

    def _convert_required(self) -> None:
        "Required fields that require conversion: hgnc_id, is_canonical, in_last_exon, strand, consequences, symbol"

        if self._full_tx_data.get("HGNC_ID"):
            hgnc_id = int(self._full_tx_data["HGNC_ID"])
        elif (
            "Gene" in self._full_tx_data
            and self._full_tx_data["Gene"] in self._ncbi_ensembl_hgnc_id
        ):
            hgnc_id = self._ncbi_ensembl_hgnc_id[self._full_tx_data["Gene"]]
        elif (
            "SYMBOL" in self._full_tx_data
            and self._full_tx_data["SYMBOL"] in self._hgnc_approved_symbol_id
        ):
            hgnc_id = self._hgnc_approved_symbol_id[self._full_tx_data["SYMBOL"]]
        else:
            if self._full_tx_data.get("SYMBOL_SOURCE") not in [
                "Clone_based_vega_gene",
                "Clone_based_ensembl_gene",
            ]:  # Silently ignore these sources, to avoid cluttering the log
                log.warning(
                    "No HGNC id found for Feature: {}, SYMBOL: {}, SYMBOL_SOURCE: {}, Gene: {}. Skipping.".format(
                        self._full_tx_data.get("Feature", "N/A"),
                        self._full_tx_data.get("SYMBOL", "N/A"),
                        self._full_tx_data.get("SYMBOL_SOURCE", "N/A"),
                        self._full_tx_data.get("Gene", "N/A"),
                    )
                )
            raise NoHgncIDError()

        self.hgnc_id = hgnc_id
        self.is_canonical = self._full_tx_data.get("CANONICAL") == "YES"

        if self._full_tx_data.get("EXON"):
            # EXON is encoded as i/N (e.g. 7/10 is exon number 7 of 10)
            parts = self._full_tx_data["EXON"].split("/")
            in_last_exon = parts[0] == parts[1]
        else:
            in_last_exon = False

        self.in_last_exon = "yes" if in_last_exon else "no"

        self.strand = int(self._full_tx_data["STRAND"])

        # All lists must be deterministic
        if self._full_tx_data.get("Consequence"):
            self.consequences = sorted(self._full_tx_data["Consequence"].split("&"))
        else:
            self.consequences = []

        if self._full_tx_data.get("SYMBOL"):
            self.symbol = self._full_tx_data["SYMBOL"]
        else:
            self.symbol = self._hgnc_approved_id_symbol[self.hgnc_id]

    def _convert_optional(self) -> None:
        "Optional fields that require conversion: dbsnp, HGVSc_*, exon_distance, coding_region_distance, protein, HGVSp"
        # Only keep dbSNP data (e.g. rs123456789)
        if self._full_tx_data.get("Existing_variation"):
            self.dbsnp = [
                t for t in self._full_tx_data["Existing_variation"].split("&") if t.startswith("rs")
            ]

        if self._full_tx_data.get("HGVSc"):
            hgvsc = self._full_tx_data["HGVSc"].split(":", 1)[-1]
            self.HGVSc = hgvsc  # Removed transcript part

            # Split away transcript part and remove long (>10 nt) insertions/deletions/duplications
            def repl_len(m):
                return "(" + str(len(m.group())) + ")"

            s = re.sub("(?<=ins)([ACGT]{10,})", repl_len, hgvsc)
            insertion = re.search("(?<=ins)([ACGT]{10,})", hgvsc)
            if insertion is not None:
                self.HGVSc_insertion = insertion.group()
            s = re.sub("(?<=[del|dup])[ACGT]{10,}", "", s)
            self.HGVSc_short = s

            exon_distance, coding_region_distance = calculate_distances(hgvsc)
            self.exon_distance = exon_distance
            self.coding_region_distance = coding_region_distance

        if self._full_tx_data.get("HGVSp"):  # Remove transcript part
            protein, hgvsp = self._full_tx_data["HGVSp"].split(":", 1)
            self.protein = protein
            self.HGVSp = hgvsp

    def as_dict(self) -> Dict[str, Any]:
        return {
            k: v
            for k, v in asdict(self).items()
            if (v is not None and not k.startswith("_")) or k in self._mandatory_fields
        }


# Symbol/ID map functions are cached so the files don't need to be constantly re-read and re-parsed
@lru_cache(1)
def get_hgnc_approved_symbol_maps() -> Tuple[Dict[int, str], Dict[str, int]]:
    this_dir = Path(__file__).parent.absolute()
    with gzip.open(this_dir / "hgnc_symbols_id.txt.gz", "rt") as hgnc_symbols:
        hgnc_approved_symbol_id: Dict[str, int] = {}
        hgnc_approved_id_symbol: Dict[int, str] = {}
        for l in hgnc_symbols:
            if l.startswith("#"):
                continue
            symbol, hgnc_id_str, approved = l.strip().split("\t")
            hgnc_id = int(hgnc_id_str)
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


@lru_cache(1)
def get_hgnc_ncbi_ensembl_map() -> Dict[str, int]:
    this_dir = Path(__file__).parent.absolute()
    with gzip.open(this_dir / "hgnc_ncbi_ensembl_geneids.txt.gz", "rt") as hgnc_ncbi_ensembl:
        ncbi_ensembl_hgnc_id: Dict[str, int] = {}
        for l in hgnc_ncbi_ensembl:
            if l.startswith("#"):
                continue
            lsplit = l.strip().split("\t")
            lsplit.extend([""] * (3 - len(lsplit)))  # Make sure line has all three columns
            hgnc_id_str, ensembl_gene, ncbi_gene = lsplit
            hgnc_id = int(hgnc_id_str)
            if ensembl_gene != "":
                assert ensembl_gene not in ncbi_ensembl_hgnc_id
                ncbi_ensembl_hgnc_id[ensembl_gene] = hgnc_id
            if ncbi_gene != "":
                assert ncbi_gene not in ncbi_ensembl_hgnc_id
                ncbi_ensembl_hgnc_id[ncbi_gene] = hgnc_id
            assert ensembl_gene == "" or ensembl_gene.startswith("ENSG")
            assert ncbi_gene == "" or int(ncbi_gene)

    return ncbi_ensembl_hgnc_id


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

HGVSC_DISTANCE_CHECK_REGEX = re.compile(
    "".join(
        [
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
    )
)


def calculate_distances(hgvsc: str) -> Tuple[Optional[int], Optional[int]]:
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

    # Region variants could extend from intron into an exon, e.g. c.*431-1_*431insA
    # The regex would then match on ed1, but not on ed2 (and return distance of -1)
    # However, if it matches on one of them, but not the other, we force the other to be "0"
    def fix_region_distance(d1: str, d2: str) -> Tuple[str, str]:
        if d1 or d2:
            d1 = d1 if d1 else "0"
            d2 = d2 if d2 else "0"
            return d1, d2
        else:
            return d1, d2

    def get_distance(pm1: str, d1: str, pm2: str, d2: str) -> int:
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

    match = HGVSC_DISTANCE_CHECK_REGEX.match(hgvsc)
    if not match:
        if hgvsc:
            log.warning("Unable to parse distances from hgvsc: {}".format(hgvsc))
        return None, None

    coding_region_distance = None
    match_data = match.groupdict()

    if match_data["region"]:
        match_data["ed1"], match_data["ed2"] = fix_region_distance(
            match_data["ed1"], match_data["ed2"]
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


class NoHgncIDError(ValueError):
    pass


class VEPConverter(AnnotationConverter):
    csq_fields: List[str]
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        pass

    def setup(self):
        assert self.meta is not None, "VEPConverter requires meta"
        self.csq_fields = self.meta["Description"].split("Format: ", 1)[1].split("|")

    def __call__(self, args: ConverterArgs) -> List[Dict[str, Any]]:
        assert isinstance(
            args.value, str
        ), f"Invalid parameter for VEPConverter: {args.value} ({type(args.value)})"
        assert self.meta is not None, "VEPConverter requires meta"

        # Prefer refseq annotations coming from the latest annotated RefSeq release (RefSeq_gff) over the
        # RefSeq interim release (RefSeq_Interim_gff) and VEP default (RefSeq).
        refseq_priority = ["RefSeq_gff", "RefSeq_Interim_gff", "RefSeq"]

        transcripts: Dict[str, TranscriptData] = {}
        no_hgnc_count = 0
        # Invert CSQ data to map to transcripts
        for raw_transcript_data in args.value.split(","):
            full_tx_data = {k: v for k, v in zip(self.csq_fields, raw_transcript_data.split("|"))}

            # Filter out non-transcripts,
            # and only include normal RefSeq or Ensembl transcripts
            if full_tx_data.get("Feature_type") != "Transcript" or not any(
                full_tx_data.get("Feature", "").startswith(t) for t in ["NM_", "NR_", "ENST"]
            ):
                continue
            try:
                tx_data = TranscriptData(full_tx_data)
            except NoHgncIDError:
                no_hgnc_count += 1
                continue

            # Check if this transcript is already processed, and if so, check if this should be overwritten
            # by incoming transcript_data based on refseq_priority. We do not want multiple annotations
            # on the same transcript. Chances are that the annotations (HGVSc, HGVSp, consequences) are equal,
            # but in a small percentage of cases the different sources can give different annotations.
            existing_tx_data = transcripts.get(tx_data.transcript)
            if existing_tx_data:
                assert (
                    existing_tx_data._source and tx_data._source
                ), "Unable to determine priority of transcript {}, as source is not defined".format(
                    tx_data.transcript
                )

                existing_source = existing_tx_data._source
                incoming_source = tx_data._source
                assert (
                    existing_source in refseq_priority and incoming_source in refseq_priority
                ), f"Transcript {tx_data.transcript} defined multiple times in annotation, but no priority defined for the sources {existing_source} and {incoming_source}"

                if refseq_priority.index(existing_source) <= refseq_priority.index(incoming_source):
                    # Existing has priority, discard incoming
                    continue

            # add new or higher priority transcript
            transcripts[tx_data.transcript] = tx_data

        # VEP output is not deterministic, but we need it to be so
        # we can compare correctly in database
        return sorted([t.as_dict() for t in transcripts.values()], key=lambda x: x["transcript"])
