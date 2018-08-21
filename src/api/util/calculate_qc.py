

def genotype_calculate_qc(allele_data, genotype_data, sample_type):
    """
    Calculates extra QC properties, for the given allele and genotype data.
    The input data should already be serialized.

    Currently adds two extra QC fields:
    - needs_verification
    - allele_ratio
    """
    qc = dict()

    #
    # Calculate allele_ratio
    #
    allele_ratio = None
    vcf_alt = allele_data['vcf_alt']

    ad_data = genotype_data['allele_depth']
    # allele_depth data is JSON in database, so assume nothing...
    if ad_data and \
       all(isinstance(v, int) for v in ad_data.values()) and \
       any(v > 0 for v in ad_data.values()) and \
       len(ad_data) > 1 and \
       vcf_alt in ad_data:

        allele_ratio = float(ad_data[vcf_alt]) / sum(ad_data.values())
        qc['allele_ratio'] = allele_ratio

    #
    # Calculate needs_verification
    #

    # Criterias:
    # (all of the following will need to be True for needs_verification to be False)
    # - SNP variant
    # - PASS filter
    # - QUAL above threshold
    # - DP above threshold
    # - allele_ratio within threshold (hom/het)
    needs_verification_checks = {
        'snp': allele_data['change_type'] == 'SNP',
        'pass': genotype_data['filter_status'] == 'PASS',
        'qual': genotype_data['variant_quality'] is not None and genotype_data['variant_quality'] > 300,
        'dp': genotype_data['sequencing_depth'] is not None and genotype_data['sequencing_depth'] > 20
    }

    if allele_ratio:
        if genotype_data['type'] == 'Homozygous':
            needs_verification_checks['allele_ratio'] = allele_ratio > 0.9
        elif genotype_data['type'] == 'Heterozygous':
            needs_verification_checks['allele_ratio'] = allele_ratio > 0.3 and allele_ratio < 0.6
        # If reference allele, failing quality on ratio makes no sense
        elif genotype_data['type'] == 'Reference':
            needs_verification_checks['allele_ratio'] = True
        else:
            needs_verification_checks['allele_ratio'] = False
    else:
        if genotype_data['type'] == 'Reference':
            needs_verification_checks['allele_ratio'] = True
        else:
            needs_verification_checks['allele_ratio'] = False

    qc['needs_verification'] = not all(needs_verification_checks.values()) and sample_type == 'HTS'
    needs_verification_checks['hts'] = sample_type == 'HTS'
    qc['needs_verification_checks'] = needs_verification_checks

    return qc
