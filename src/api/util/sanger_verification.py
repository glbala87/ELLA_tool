import numbers


class SangerVerification(object):

    def check_criterias(self, allele):
        """
        :param allele: Allele to check if matches criterias
        :type allele: Dict as outputted from AnnotationProcessor
        """
        criteria_check = dict()

        # check it is a SNP
        # If changing or removing this, review the AD code further down
        criteria_check['SNP'] = allele['changeType'] == 'SNP'

        # DP > 20 x
        if isinstance(allele['genotype']['sequencingDepth'], numbers.Real) and \
           allele['genotype']['sequencingDepth'] > 20:
            criteria_check['DP'] = True
        else:
            criteria_check['DP'] = False

        # FILTER = PASS
        criteria_check['FILTER'] = allele['genotype']['filterStatus'] == 'PASS'

        # QUAL > 300
        if isinstance(allele['genotype']['variantQuality'], numbers.Real) and \
           allele['genotype']['variantQuality'] > 300:
            criteria_check['QUAL'] = True
        else:
            criteria_check['QUAL'] = False

        # Check AD ratio
        # Calculated as: (Depth of alleleDepth for our allele)/(Total allele depth)
        # allele ratio criteria: HET: between 0.3-0.6, HOM: > 0.9.

        def hom_criteria(ratio):
            return ratio > 0.9

        def het_criteria(ratio):
            return ratio > 0.3 and ratio < 0.6

        criteria_func = hom_criteria if allele['genotype']['homozygous'] else het_criteria

        # This only works for SNP, for indels the changeTo has the REF part stripped off
        # by the deposit script, so we can't find the right alleleDepth.
        # We only need to support SNPs right now

        # If no allele depth data, fail check
        if not allele['genotype']['alleleDepth']:
            criteria_check['AD'] = False
        elif allele['changeType'] == 'SNP':
            allele_depth = allele['genotype']['alleleDepth'][allele['changeTo']]
            total_depth = sum(allele['genotype']['alleleDepth'].values())
            ratio = float(allele_depth)/total_depth
            criteria_check['AD'] = criteria_func(ratio)

        return criteria_check

    def needs_verification(self, allele):
        criteria_check = self.check_criterias(allele)
        return not all(criteria_check.values())
