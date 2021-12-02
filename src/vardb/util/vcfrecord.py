from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union, List
import cyvcf2
import logging
import numpy as np
from os.path import commonprefix

log = logging.getLogger(__name__)

# have to re-declare here since only exist in cyvcf2 stub and fails on execution
Text = Union[str, bytes]
Primitives = Union[int, float, bool, Text]


def _numpy_unknown_to_none(a: np.ndarray) -> list:
    """
    Unknown values ('.') in integer arrays are assigned as '-inf' (e.g. for in32 the value is -2^31)
    Convert array to list, and replace these values with None
    """
    b = a.tolist()
    n = max(a.shape)
    indices = zip(*np.where(a < np.iinfo(a.dtype).min + n))

    def set_value(x, i, value):
        "Set value in nested lists"
        if len(i) > 1:
            x = set_value(x[i[0]], i[1:], value)
        else:
            x[i[0]] = value

    for idx in indices:
        set_value(b, idx, None)

    return b


def numpy_to_list(a: Optional[np.ndarray]) -> Optional[List]:
    if a is None:
        return None
    if np.issubdtype(a.dtype, np.integer):
        return _numpy_unknown_to_none(a)
    else:
        return a.tolist()


def commonsuffix(v: List[Union[str, bytes]]) -> Union[str, bytes]:
    "Common suffix is the same as the reversed common prefix of the reversed string"
    # mypy complains about expecting os.PathLike, but commonprefix handles that implicitly
    return commonprefix([x[::-1] for x in v])[::-1]  # type: ignore


change_type_from_sv_alt_field = {
    "<DUP>": "dup",
    "<DUP:TANDEM>": "dup_tandem",
    "<DEL>": "del",
    "<DEL:ME>": "del_me",
}


class VCFRecord(object):
    variant: cyvcf2.Variant
    samples: Sequence[str]
    meta: Mapping[str, Any]
    _allele: Optional[Mapping[str, Any]]

    def __init__(self, variant: cyvcf2.Variant, samples: Sequence[str], meta: Mapping[str, Any]):
        self.variant = variant
        self.samples = samples
        self.meta = meta
        self._allele = None

    @property
    def allele(self) -> Mapping[str, Any]:
        if self._allele is None:
            self._allele = self._build_allele("GRCh37")
        return self._allele

    def get_allele(self, alleles: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        # Note: We need this, as the allele can be instrumented with id from importers.bulk_insert_nonexisting
        # TODO: Investigate how we can avoid dictionaries, and use vardb.datamodel.allele.Allele objects instead
        for allele in alleles:
            if (
                allele["chromosome"] == self.variant.CHROM
                and allele["vcf_pos"] == self.variant.POS
                and allele["vcf_ref"] == self.variant.REF
                and allele["vcf_alt"] == self.variant.ALT[0]
            ):
                return allele
        return None

    def _sample_index(self, sample_name: str) -> int:
        return self.samples.index(sample_name)

    def sv_type(self) -> Optional[str]:
        return self.variant.INFO.get("SVTYPE")

    def sv_change_type(self, vcf_alt: Union[bytes, str]) -> str:
        if vcf_alt in change_type_from_sv_alt_field:
            return change_type_from_sv_alt_field[str(vcf_alt)]

        elif self.sv_type() == "DEL":
            return "del"
        elif self.sv_type() == "DUP":
            return "dup"
        else:
            raise Exception(
                f"ELLA only supports ALT=<DUP>,<DUP:TANDEM>,<DEL> or SVTYPE of value: DEL and DUP, {self.sv_type()} is not supported"
            )

    def _sv_len(self) -> int:
        return int(self.variant.INFO["SVLEN"])

    def _sv_open_end_position(self, pos: int, change_type: str) -> int:

        if change_type == "dup" or change_type == "dup_tandem" or change_type == "ins":
            return pos + 1
        else:
            return pos + abs(self._sv_len())

    def _snv_allele_info(self, pos, ref, alt) -> Tuple[int, int, str, int, str, str]:
        # Remove common suffix
        # (with ref, alt = ("AGAA", "ACAA") change to ref, alt = ("AG", "AC"))
        N_suffix = len(commonsuffix([ref, alt]))
        if N_suffix > 0:
            ref, alt = ref[:-N_suffix], alt[:-N_suffix]

        # Remove common prefix and offset position
        # (with pos, ref, alt = (123, "AG", "AC") change to pos, ref, alt = (124, "G", "C"))
        N_prefix = len(commonprefix([ref, alt]))
        ref, alt = ref[N_prefix:], alt[N_prefix:]
        pos += N_prefix

        if len(ref) == len(alt) == 1:
            change_type = "SNP"
            start_position = pos
            open_end_position = pos + 1
        elif len(ref) >= 1 and len(alt) >= 1:
            assert len(ref) > 1 or len(alt) > 1
            change_type = "indel"
            start_position = pos
            open_end_position = pos + len(ref)
        elif len(ref) < len(alt):
            assert ref == ""
            change_type = "ins"
            # An insertion is shifted one base 1 because of same prefix above,
            # but the insertion is done between the reference allele (at pos-1) and the subsequent allele (at pos)
            start_position = pos - 1
            # Insertions have no span in the reference genome
            open_end_position = pos
        elif len(ref) > len(alt):
            assert alt == ""
            change_type = "del"
            start_position = pos
            open_end_position = pos + len(ref)
        else:
            raise ValueError("Unable to determine allele from ref/alt={}/{}".format(ref, alt))

        if change_type == "ins":
            allele_length = 1
        else:
            allele_length = max(len(ref), len(alt))

        return start_position, open_end_position, change_type, allele_length, ref, alt

    def _cnv_allele_info(self, pos, vcf_ref, vcf_alt) -> Tuple[int, int, str, int, str, str]:
        start_position = pos
        change_type = self.sv_change_type(vcf_alt)
        open_end_position = self._sv_open_end_position(pos, change_type)
        allele_length = abs(self._sv_len())
        ref = ""
        alt = ""
        if vcf_alt not in change_type_from_sv_alt_field:
            ref = vcf_ref
            alt = vcf_alt

        return start_position, open_end_position, change_type, allele_length, ref, alt

    def _build_allele(self, ref_genome: str) -> Mapping[str, Any]:
        vcf_ref, vcf_alt, vcf_pos = (
            self.variant.REF,
            self.variant.ALT[0],
            self.variant.POS,
        )

        pos = vcf_pos - 1

        if self.sv_type() is None:
            (
                start_position,
                open_end_position,
                change_type,
                allele_length,
                ref,
                alt,
            ) = self._snv_allele_info(pos, vcf_ref, vcf_alt)
            caller_type = "snv"
        else:
            (
                start_position,
                open_end_position,
                change_type,
                allele_length,
                ref,
                alt,
            ) = self._cnv_allele_info(pos, vcf_ref, vcf_alt)
            caller_type = "cnv"
        allele = {
            "genome_reference": ref_genome,
            "chromosome": self.variant.CHROM,
            "start_position": start_position,
            "open_end_position": open_end_position,
            "change_type": change_type,
            "change_from": ref,
            "change_to": alt,
            "length": allele_length,
            "vcf_pos": vcf_pos,
            "vcf_ref": vcf_ref,
            "vcf_alt": vcf_alt,
            "caller_type": caller_type,
        }

        return allele

    def get_raw_filter(self) -> str:
        """Need to implement this here, as cyvcf2 does not distinguish between 'PASS' and '.' (both return None).
        Therefore, we need to parse the VCF line to get the raw filter status."""
        return str(self.variant).split("\t")[6]

    def sample_genotype(self, sample_name: str) -> Tuple[int, ...]:
        return tuple(self.variant.genotypes[self._sample_index(sample_name)][:-1])

    def has_allele(self, sample_name: str) -> bool:
        gt = self.sample_genotype(sample_name)
        vcf_alt = self.variant.ALT[0]
        if (
            self.sv_type()
            and (
                self.sv_change_type(vcf_alt) == "dup"
                or self.sv_change_type(vcf_alt) == "dup_tandem"
            )
            and gt == (-1, -1)
        ):
            return True
        else:
            return max(gt) == 1

    def get_format_sample(
        self, property: str, sample_name: str, scalar: bool = False
    ) -> Optional[Union[Iterable[Any], int]]:

        if property == "GT":
            return self.sample_genotype(sample_name)
        else:
            if property not in self.variant.FORMAT:
                return None
            prop = self.variant.format(property)
            if prop is None:
                return None

            ret = numpy_to_list(prop[self._sample_index(sample_name)])
            assert ret
            if scalar:
                assert len(ret) == 1
                return ret[0]
            else:
                return ret

    def get_block_id(self) -> Optional[str]:
        return self.variant.INFO.get("OLD_MULTIALLELIC")

    def is_multiallelic(self) -> bool:
        return self.get_block_id() is not None

    def is_sample_multiallelic(self, sample_name: str) -> bool:
        return self.is_multiallelic() and bool(set(self.sample_genotype(sample_name)) - set([0, 1]))

    def annotation(
        self,
    ) -> Dict[str, Union[Primitives, Tuple[Primitives, ...]]]:
        return dict(x for x in self.variant.INFO)

    def __str__(self):
        s = repr(self.variant)

        if self.samples:
            genotypes = []
            for i, x in enumerate(self.variant.gt_bases):
                genotypes.append(f"{x} ({str(self.samples[i])})")

            s += f" - Genotypes: {', '.join(genotypes)}"
        return s
