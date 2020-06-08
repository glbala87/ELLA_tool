from math import log10

MUTATION_PRIOR = 1e-8
DEFAULT_FREQ = 0.1


def denovo_probability(pl_c, pl_f, pl_m, is_x_minus_par, proband_male, denovo_mode):
    """
    Compute a posteriori denovo probability given phred scaled genotype likelihoods for genotypes [0/0, 1/0, 1/1]
    Denovo mode is a three-tuple of the called genotypes for father, mother and proband respectively,
    as indexes of the above genotypes. Examples:
     - denovo_mode=[0,0,1] -> Compute probability of proband being heterozygous given both parents called homozygous reference
     - denovo_mode=[0,1,2] -> Compute probability of proband being homozygous given over parent called as heterozygous, and one as homozygous reference

    Based on denovo probability computation from FILTUS (see supporting material):
    https://academic.oup.com/bioinformatics/article/32/10/1592/1743466
    """

    # A priori probability of mutation
    def priors(is_x_minus_par):
        logfr = [log10(1 - DEFAULT_FREQ), log10(DEFAULT_FREQ)]
        log_hardy_weinberg = [2 * logfr[0], log10(2) + logfr[0] + logfr[1], 2 * logfr[1]]
        if is_x_minus_par:
            return log_hardy_weinberg, logfr
        else:
            return log_hardy_weinberg, log_hardy_weinberg

    # Probability of child getting alleles from mother/father given genotypes
    def _single_transmit(parent, child):
        if child in parent and parent[0] == parent[1]:
            # Probability of getting an allele from homozygous parent
            return 1 - MUTATION_PRIOR
        elif child in parent:
            # Probability of getting an allele from heterozygous parent
            return 0.5
        else:
            # Probability of a denovo mutation
            return MUTATION_PRIOR

    class TrioTransmit(object):
        def __init__(self, is_x_minus_par, proband_male):
            self.is_x_minus_par = is_x_minus_par
            self.proband_male = proband_male

            if self.is_x_minus_par and self.proband_male:
                # No transmission from father to boy on X (minus PAR) chromosome
                self.transmit_father = None
            elif self.is_x_minus_par and not self.proband_male:
                # Since father only has one copy to inherit from, chance of inheriting is either very high (father has allele)
                # or very low (father does not have allele)
                self.transmit_father = lambda f, c: 1 - MUTATION_PRIOR if f == c else MUTATION_PRIOR
            else:
                self.transmit_father = _single_transmit

            self.transmit_mother = _single_transmit

        def __call__(self, father, mother, child):
            if self.is_x_minus_par and self.proband_male:
                # No transmission from father to boy on X (minus PAR) chromosome
                return self.transmit_mother(mother, child[0])
            elif child[0] == child[1]:
                # Child is homozygous, probability of inheriting from both mother and father
                return self.transmit_father(father, child[0]) * self.transmit_mother(
                    mother, child[0]
                )
            else:
                # Child is heterozygous, probability of inheriting from mother + probability of inheriting from father
                return self.transmit_father(father, child[0]) * self.transmit_mother(
                    mother, child[1]
                ) + self.transmit_father(father, child[0]) * self.transmit_mother(mother, child[1])

    class LogTransmissionMatrix(object):
        def __init__(self, is_x_minus_par, proband_male):
            gt = [(0, 0), (0, 1), (1, 1)]
            gtx = [(0,), (1,)]

            if is_x_minus_par and proband_male:
                self.child_gt = gtx
                self.father_gt = gtx
            elif is_x_minus_par and not proband_male:
                self.father_gt = gtx
                self.child_gt = gt
            else:
                self.father_gt = gt
                self.child_gt = gt
            self.mother_gt = gt
            self.trio_transmit = TrioTransmit(is_x_minus_par, proband_male)

        def __call__(self, f, m, c):
            return log10(self.trio_transmit(self.father_gt[f], self.mother_gt[m], self.child_gt[c]))

    # Remove PL for genotype 0/1 if X chromosome for father and proband if proband is male
    if is_x_minus_par:
        pl_f = [pl_f[0], pl_f[2]]
        if proband_male:
            pl_c = [pl_c[0], pl_c[2]]

    mo_prior, fa_prior = priors(is_x_minus_par)
    log_transmission_matrix = LogTransmissionMatrix(is_x_minus_par, proband_male)

    # Compute relative likelihoods of all genotype combinations, using the phred scaled genotype likelihoods
    sum_liks = 0
    for fi, _pl_f in enumerate(pl_f):
        for mi, _pl_m in enumerate(pl_m):
            for ci, _pl_c in enumerate(pl_c):
                lh = (
                    fa_prior[fi]
                    + mo_prior[mi]
                    + log_transmission_matrix(fi, mi, ci)
                    - (_pl_f + _pl_m + _pl_c) / 10
                )
                sum_liks += pow(10, lh)

    # Compute likelihood of the given denovo mode
    f, m, c = denovo_mode
    lh = pow(
        10,
        fa_prior[f]
        + mo_prior[m]
        + log_transmission_matrix(f, m, c)
        - (pl_f[f] + pl_m[m] + pl_c[c]) / 10,
    )

    # Normalize likelihood to probability
    return lh / sum_liks
