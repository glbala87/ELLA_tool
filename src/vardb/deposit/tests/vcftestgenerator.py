from hypothesis import assume
from hypothesis import strategies as st


ALLELE_ALT = "T"


def variant():
    global ALLELE_ALT
    ALLELE_ALT += "T"
    return {"ALT": ALLELE_ALT, "QUAL": 5000, "FILTER": "PASS"}


@st.composite
def block_strategy(draw, samples):
    """
    Generates a multiallelic "block" for multiple samples, by creating a composed genotype and then decomposing it.

    Returns a list where each element corresponds to the samples genotypes for a variant.
    """

    block = []
    ploidity = {sample: draw(st.sampled_from([2, 1])) for sample in samples}
    block_size = draw(st.integers(min_value=2, max_value=len(samples) * 2))

    def decompose_genotype(gt):
        """
        Creates decomposed genotypes for a given composed genotype.

        Examples:
        (0, 0) => [(0, 0)]]
        (0, 1) => [(0, 1)]]
        (1, 1) => [(1, 1)]]
        (2, 1) => [(".", 1), (1, ".")]]
        (0, 2) => [(0, "."), (0, 1)]]
        (1, 3) => [(1, "."), (".", "."), (".", 1)]]

        """
        decomposed = []
        if max(gt) <= 1:
            return [gt]

        num_genotypes = max(gt)
        ploidity = len(gt)
        is_reference = [False] * ploidity

        for i in range(1, num_genotypes + 1):
            x = [None] * ploidity
            for j in range(ploidity):
                if gt[j] == 0:
                    is_reference[j] = True

                if i == gt[j] and i > 0:
                    x[j] = 1
                elif is_reference[j]:
                    x[j] = 0
                else:
                    x[j] = "."

            decomposed.append(tuple(x))
        return decomposed

    sample_genotypes = {}
    for sample in samples:
        phasing = draw(st.sampled_from(["/", "|"]))

        # Create a composed genotype
        gt = draw(
            st.tuples(*[st.integers(min_value=0, max_value=block_size - 1)] * ploidity[sample])
        )

        # Decompose genotype
        decomposed = decompose_genotype(gt)

        # Add "filler" genotypes for remaining records
        while len(decomposed) < block_size:
            filler = []
            for i in range(ploidity[sample]):
                if any(g[i] == 0 for g in decomposed):
                    assert all(g[i] == 0 for g in decomposed)
                    filler.append(0)
                else:
                    filler.append(".")
            decomposed.append(tuple(filler))

        # Debug: print decomposed genotype
        # print(sample, gt, "-->", decomposed)

        # Create genotype strings
        sample_genotypes[sample] = [phasing.join(str(x) for x in dgt) for dgt in decomposed]

    for record in range(block_size):
        record_samples = []
        variant_in_record = False
        for sample in samples:
            gt = sample_genotypes[sample][record]
            if "1" in gt:
                variant_in_record = True

            # Draw from a limited pool to avoid too many combinations
            record_samples.append(
                {
                    "GT": gt,
                    "AD": "{},{}".format(
                        draw(st.integers(min_value=0, max_value=4)),
                        draw(st.integers(min_value=100, max_value=104)),
                    ),
                    "DP": draw(st.integers(min_value=100, max_value=103)),
                    "GQ": draw(st.integers(min_value=90, max_value=93)),
                    "PL": "{},{},{}".format(
                        draw(st.integers(min_value=0, max_value=4)),
                        draw(st.integers(min_value=50, max_value=54)),
                        draw(st.integers(min_value=100, max_value=104)),
                    ),
                }
            )

        # Skip block if it doesn't contain variants for any of the samples
        if variant_in_record:
            block.append(record_samples)

    assume(block)

    return block


@st.composite
def pedigree_strategy(draw, sample_names):
    """
    Samples are implicitly: <proband>, <father>, <mother>, <sibling1>, ...
    """

    # For single sample, ped file isn't needed
    if len(sample_names) == 1:
        return {sample_names[0]: {"affected": "2", "proband": "1", "sex": None}}

    father_sample = None
    mother_sample = None
    if len(sample_names) > 1:
        father_sample = sample_names[1]
    if len(sample_names) > 2:
        mother_sample = sample_names[2]

    ped_infos = dict()
    if len(sample_names) > 1:
        for idx, sample_name in enumerate(sample_names):
            is_proband = idx == 0
            is_parents = idx == 1 or idx == 2
            is_sibling = idx > 2

            affected = "1"
            if is_proband:
                affected = "2"
                sex = draw(st.sampled_from(["1", "2"]))
            elif is_sibling:
                affected = "2" if draw(st.booleans()) else "1"
                sex = draw(st.sampled_from(["1", "2"]))
            elif is_parents:
                if idx == 1:
                    sex = "1"
                elif idx == 2:
                    sex = "2"

            ped_info = {
                "fam": "TEST_FAM",
                "sample": sample_name,
                "father": father_sample if is_proband and father_sample else "0",
                "mother": mother_sample if is_proband and mother_sample else "0",
                "sex": sex,
                "affected": affected,
                "proband": "1" if is_proband else "0",
            }
            ped_infos[sample_name] = ped_info

    return ped_infos


@st.composite
def vcf_family_strategy(draw, max_num_samples):
    num_samples = draw(st.integers(min_value=1, max_value=max_num_samples))

    base_names = ["PROBAND", "FATHER", "MOTHER"]
    sample_names = base_names[:num_samples]

    if num_samples > 3:
        sample_names += ["SIBLING_{}".format(idx - 3) for idx in range(3, num_samples)]
    sample_formats_block = draw(block_strategy(sample_names))

    # Create variants for each line in block
    variants = [variant() for _ in sample_formats_block]

    # Add OLD_MULTIALLELIC to annotation if this block is multiallelic
    # (it doesn't matter what this is, as long as it is unique for the specific block)
    if len(sample_formats_block) > 1:
        block_id = draw(st.uuids())
        for v in variants:
            v["INFO"] = {"OLD_MULTIALLELIC": block_id}

    ped_info = draw(pedigree_strategy(sample_names))
    return variants, sample_formats_block, sample_names, ped_info
