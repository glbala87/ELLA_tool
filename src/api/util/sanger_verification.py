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
        criteria_check['SNP'] = allele['change_type'] == 'SNP'

        # DP > 40 x
        if isinstance(allele['genotype']['sequencing_depth'], numbers.Real) and \
           allele['genotype']['sequencing_depth'] > 40:
            criteria_check['DP'] = True
        else:
            criteria_check['DP'] = False

        # FILTER = PASS
        criteria_check['FILTER'] = allele['genotype']['filter_status'] == 'PASS'

        # QUAL > 300
        if isinstance(allele['genotype']['variant_quality'], numbers.Real) and \
           allele['genotype']['variant_quality'] > 300:
            criteria_check['QUAL'] = True
        else:
            criteria_check['QUAL'] = False

        # Check AD ratio
        # Calculated as: (Depth of allele_depth for our allele)/(Total allele depth)
        # allele ratio criteria: HET: between 0.3-0.6, HOM: > 0.9.

        def hom_criteria(ratio):
            return ratio > 0.9

        def het_criteria(ratio):
            return ratio > 0.3 and ratio < 0.6

        criteria_func = hom_criteria if allele['genotype']['homozygous'] else het_criteria

        # This only works for SNP, for indels the change_to has the REF part stripped off
        # by the deposit script, so we can't find the right allele_depth.
        # We only need to support SNPs right now

        # If no allele depth data, fail check
        if not allele['genotype']['allele_depth']:
            criteria_check['AD'] = False
        elif allele['change_type'] == 'SNP':
            allele_depth = allele['genotype']['allele_depth'][allele['change_to']]
            total_depth = sum(allele['genotype']['allele_depth'].values())
            ratio = float(allele_depth)/total_depth
            criteria_check['AD'] = criteria_func(ratio)

        return criteria_check

    def needs_verification(self, allele):
        criteria_check = self.check_criterias(allele)
        return not all(criteria_check.values())
