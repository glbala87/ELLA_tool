import logging
from hypothesis import assume
from hypothesis import strategies as st

log = logging.getLogger(__name__)

VCF_TEMPLATE = """##fileformat=VCFv4.1
##FILTER=<ID=FSFilter,Description="FS > 200.0">
##FILTER=<ID=LowQual,Description="Low quality">
##FILTER=<ID=PASS,Description="All filters passed">
##FILTER=<ID=QDFilter,Description="QD < 2.0">
##FILTER=<ID=ReadPosFilter,Description="ReadPosRankSum < -20.0">
##FILTER=<ID=VQSRTrancheSNP99.00to99.90,Description="Truth sensitivity tranche level for SNP model at VQS Lod: -14.4933 <= x < -1.4905">
##FILTER=<ID=VQSRTrancheSNP99.90to100.00,Description="Truth sensitivity tranche level for SNP model at VQS Lod: -3111.7055 <= x < -14.4933">
##FILTER=<ID=VQSRTrancheSNP99.90to100.00+,Description="Truth sensitivity tranche level for SNP model at VQS Lod < -3111.7055">
##INFO=<ID=AC,Number=A,Type=Integer,Description="Allele count in genotypes, for each ALT allele, in the same order as listed">
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency, for each ALT allele, in the same order as listed">
##INFO=<ID=AN,Number=1,Type=Integer,Description="Total number of alleles in called genotypes">
##INFO=<ID=BIC__BRCA1__A,Number=.,Type=String,Description="BIC field A (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__AA_Change,Number=.,Type=String,Description="BIC field AA_Change (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Accession_Number,Number=.,Type=String,Description="BIC field Accession_Number (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Addition_Information,Number=.,Type=String,Description="BIC field Addition_Information (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Base_Change,Number=.,Type=String,Description="BIC field Base_Change (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__C,Number=.,Type=String,Description="BIC field C (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Clinically_Important,Number=.,Type=String,Description="BIC field Clinically_Important (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Codon,Number=.,Type=String,Description="BIC field Codon (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Contact_Person,Number=.,Type=String,Description="BIC field Contact_Person (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Creation_Date,Number=.,Type=String,Description="BIC field Creation_Date (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Depositor,Number=.,Type=String,Description="BIC field Depositor (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Designation,Number=.,Type=String,Description="BIC field Designation (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Detection_Method,Number=.,Type=String,Description="BIC field Detection_Method (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Ethnicity,Number=.,Type=String,Description="BIC field Ethnicity (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Exon,Number=.,Type=String,Description="BIC field Exon (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__G,Number=.,Type=String,Description="BIC field G (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__G_or_S,Number=.,Type=String,Description="BIC field G_or_S (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Genotype,Number=.,Type=String,Description="BIC field Genotype (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__HGVS_Protein,Number=.,Type=String,Description="BIC field HGVS_Protein (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__HGVS_cDNA,Number=.,Type=String,Description="BIC field HGVS_cDNA (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__ID_Number,Number=.,Type=String,Description="BIC field ID_Number (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Mutation_Effect,Number=.,Type=String,Description="BIC field Mutation_Effect (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Mutation_Type,Number=.,Type=String,Description="BIC field Mutation_Type (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__NT,Number=.,Type=String,Description="BIC field NT (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Nationality,Number=.,Type=String,Description="BIC field Nationality (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Notes,Number=.,Type=String,Description="BIC field Notes (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Number_Reported,Number=.,Type=String,Description="BIC field Number_Reported (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Patient_Sample_Source,Number=.,Type=String,Description="BIC field Patient_Sample_Source (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Proband_Tumor_Type,Number=.,Type=String,Description="BIC field Proband_Tumor_Type (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__Reference,Number=.,Type=String,Description="BIC field Reference (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__T,Number=.,Type=String,Description="BIC field T (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__dbSNP,Number=.,Type=String,Description="BIC field dbSNP (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA1__nChr,Number=.,Type=String,Description="BIC field nChr (from /anno/data/variantDBs/bic/bic_brca1_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__A,Number=.,Type=String,Description="BIC field A (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__AA_Change,Number=.,Type=String,Description="BIC field AA_Change (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Accession_Number,Number=.,Type=String,Description="BIC field Accession_Number (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Addition_Information,Number=.,Type=String,Description="BIC field Addition_Information (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Base_Change,Number=.,Type=String,Description="BIC field Base_Change (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__C,Number=.,Type=String,Description="BIC field C (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Clinically_Important,Number=.,Type=String,Description="BIC field Clinically_Important (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Codon,Number=.,Type=String,Description="BIC field Codon (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Contact_Person,Number=.,Type=String,Description="BIC field Contact_Person (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Creation_Date,Number=.,Type=String,Description="BIC field Creation_Date (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Depositor,Number=.,Type=String,Description="BIC field Depositor (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Designation,Number=.,Type=String,Description="BIC field Designation (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Detection_Method,Number=.,Type=String,Description="BIC field Detection_Method (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Ethnicity,Number=.,Type=String,Description="BIC field Ethnicity (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Exon,Number=.,Type=String,Description="BIC field Exon (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__G,Number=.,Type=String,Description="BIC field G (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__G_or_S,Number=.,Type=String,Description="BIC field G_or_S (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Genotype,Number=.,Type=String,Description="BIC field Genotype (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__HGVS_Protein,Number=.,Type=String,Description="BIC field HGVS_Protein (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__HGVS_cDNA,Number=.,Type=String,Description="BIC field HGVS_cDNA (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__ID_Number,Number=.,Type=String,Description="BIC field ID_Number (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Mutation_Effect,Number=.,Type=String,Description="BIC field Mutation_Effect (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Mutation_Type,Number=.,Type=String,Description="BIC field Mutation_Type (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__NT,Number=.,Type=String,Description="BIC field NT (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Nationality,Number=.,Type=String,Description="BIC field Nationality (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Notes,Number=.,Type=String,Description="BIC field Notes (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Number_Reported,Number=.,Type=String,Description="BIC field Number_Reported (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Patient_Sample_Source,Number=.,Type=String,Description="BIC field Patient_Sample_Source (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Proband_Tumor_Type,Number=.,Type=String,Description="BIC field Proband_Tumor_Type (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__Reference,Number=.,Type=String,Description="BIC field Reference (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__T,Number=.,Type=String,Description="BIC field T (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__dbSNP,Number=.,Type=String,Description="BIC field dbSNP (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BIC__BRCA2__nChr,Number=.,Type=String,Description="BIC field nChr (from /anno/data/variantDBs/bic/bic_brca2_norm.vcf.gz)">
##INFO=<ID=BaseQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt Vs. Ref base qualities">
##INFO=<ID=CCC,Number=1,Type=Integer,Description="Number of called chromosomes">
##INFO=<ID=CLINVARJSON,Number=1,Type=String,Description="Base 16-encoded JSON representation of metadata associated with this variant. Read back as lambda x: json.loads(base64.b16decode(x)). (from /anno/data/variantDBs/clinvar/clinvar_20171113_norm.vcf.gz)">
##INFO=<ID=CSQ,Number=.,Type=String,Description="Consequence annotations from Ensembl VEP. Format: Allele|Consequence|IMPACT|SYMBOL|Gene|Feature_type|Feature|BIOTYPE|EXON|INTRON|HGVSc|HGVSp|cDNA_position|CDS_position|Protein_position|Amino_acids|Codons|Existing_variation|ALLELE_NUM|DISTANCE|STRAND|SYMBOL_SOURCE|HGNC_ID|CANONICAL|CCDS|ENSP|REFSEQ_MATCH|SIFT|PolyPhen|DOMAINS|GMAF|AFR_MAF|AMR_MAF|ASN_MAF|EAS_MAF|EUR_MAF|SAS_MAF|AA_MAF|EA_MAF|CLIN_SIG|SOMATIC|PUBMED|MOTIF_NAME|MOTIF_POS|HIGH_INF_POS|MOTIF_SCORE_CHANGE">
##INFO=<ID=CUSTOM1,Number=.,Type=String,Description="/anno/data/repeatMasker/repeatMasker_hg19.20150508.reformat.sorted.bed.gz (exact)">
##INFO=<ID=ClippingRankSum,Number=1,Type=Float,Description="Z-score From Wilcoxon rank sum test of Alt vs. Ref number of hard clipped bases">
##INFO=<ID=DB,Number=0,Type=Flag,Description="dbSNP Membership">
##INFO=<ID=DP,Number=1,Type=Integer,Description="Approximate read depth; some reads may have been filtered">
##INFO=<ID=DS,Number=0,Type=Flag,Description="Were any of the samples downsampled?">
##INFO=<ID=END,Number=1,Type=Integer,Description="Stop position of the interval">
##INFO=<ID=EXAC__AC,Number=A,Type=Integer,Description="Allele count in genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_AFR,Number=A,Type=Integer,Description="African/African American Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_AMR,Number=A,Type=Integer,Description="American Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_Adj,Number=A,Type=Integer,Description="Adjusted Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_EAS,Number=A,Type=Integer,Description="East Asian Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_FIN,Number=A,Type=Integer,Description="Finnish Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_Hemi,Number=A,Type=Integer,Description="Adjusted Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_Het,Number=A,Type=Integer,Description="Adjusted Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_Hom,Number=A,Type=Integer,Description="Adjusted Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_NFE,Number=A,Type=Integer,Description="Non-Finnish European Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_OTH,Number=A,Type=Integer,Description="Other Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AC_SAS,Number=A,Type=Integer,Description="South Asian Allele Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AF,Number=A,Type=Float,Description="Allele Frequency, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN,Number=1,Type=Integer,Description="Total number of alleles in called genotypes (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_AFR,Number=1,Type=Integer,Description="African/African American Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_AMR,Number=1,Type=Integer,Description="American Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_Adj,Number=1,Type=Integer,Description="Adjusted Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_EAS,Number=1,Type=Integer,Description="East Asian Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_FIN,Number=1,Type=Integer,Description="Finnish Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_NFE,Number=1,Type=Integer,Description="Non-Finnish European Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_OTH,Number=1,Type=Integer,Description="Other Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__AN_SAS,Number=1,Type=Integer,Description="South Asian Chromosome Count (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__BaseQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt Vs. Ref base qualities (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__CCC,Number=1,Type=Integer,Description="Number of called chromosomes (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__ClippingRankSum,Number=1,Type=Float,Description="Z-score From Wilcoxon rank sum test of Alt vs. Ref number of hard clipped bases (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__DB,Number=0,Type=Flag,Description="dbSNP Membership (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__DP,Number=1,Type=Integer,Description="Approximate read depth; some reads may have been filtered (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__DP_HIST,Number=R,Type=String,Description="Histogram for DP; Mids: 2.5|7.5|12.5|17.5|22.5|27.5|32.5|37.5|42.5|47.5|52.5|57.5|62.5|67.5|72.5|77.5|82.5|87.5|92.5|97.5 (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__DS,Number=0,Type=Flag,Description="Were any of the samples downsampled? (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__END,Number=1,Type=Integer,Description="Stop position of the interval (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__FS,Number=1,Type=Float,Description="Phred-scaled p-value using Fisher's exact test to detect strand bias (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__GQ_HIST,Number=R,Type=String,Description="Histogram for GQ; Mids: 2.5|7.5|12.5|17.5|22.5|27.5|32.5|37.5|42.5|47.5|52.5|57.5|62.5|67.5|72.5|77.5|82.5|87.5|92.5|97.5 (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__GQ_MEAN,Number=1,Type=Float,Description="Mean of all GQ values (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__GQ_STDDEV,Number=1,Type=Float,Description="Standard deviation of all GQ values (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__HWP,Number=1,Type=Float,Description="P value from test of Hardy Weinberg Equilibrium (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__HaplotypeScore,Number=1,Type=Float,Description="Consistency of the site with at most two segregating haplotypes (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_AFR,Number=A,Type=Integer,Description="African/African American Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_AMR,Number=A,Type=Integer,Description="American Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_EAS,Number=A,Type=Integer,Description="East Asian Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_FIN,Number=A,Type=Integer,Description="Finnish Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_NFE,Number=A,Type=Integer,Description="Non-Finnish European Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_OTH,Number=A,Type=Integer,Description="Other Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hemi_SAS,Number=A,Type=Integer,Description="South Asian Hemizygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_AFR,Number=.,Type=Integer,Description="African/African American Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_AMR,Number=.,Type=Integer,Description="American Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_EAS,Number=.,Type=Integer,Description="East Asian Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_FIN,Number=.,Type=Integer,Description="Finnish Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_NFE,Number=.,Type=Integer,Description="Non-Finnish European Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_OTH,Number=.,Type=Integer,Description="Other Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Het_SAS,Number=.,Type=Integer,Description="South Asian Heterozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_AFR,Number=A,Type=Integer,Description="African/African American Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_AMR,Number=A,Type=Integer,Description="American Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_EAS,Number=A,Type=Integer,Description="East Asian Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_FIN,Number=A,Type=Integer,Description="Finnish Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_NFE,Number=A,Type=Integer,Description="Non-Finnish European Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_OTH,Number=A,Type=Integer,Description="Other Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__Hom_SAS,Number=A,Type=Integer,Description="South Asian Homozygous Counts (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__InbreedingCoeff,Number=1,Type=Float,Description="Inbreeding coefficient as estimated from the genotype likelihoods per-sample when compared against the Hardy-Weinberg expectation (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__MLEAC,Number=A,Type=Integer,Description="Maximum likelihood expectation (MLE) for the allele counts (not necessarily the same as the AC), for each ALT allele, in the same order as listed (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__MLEAF,Number=A,Type=Float,Description="Maximum likelihood expectation (MLE) for the allele frequency (not necessarily the same as the AF), for each ALT allele, in the same order as listed (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__MQ,Number=1,Type=Float,Description="RMS Mapping Quality (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__MQ0,Number=1,Type=Integer,Description="Total Mapping Quality Zero Reads (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__MQRankSum,Number=1,Type=Float,Description="Z-score From Wilcoxon rank sum test of Alt vs. Ref read mapping qualities (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__NCC,Number=1,Type=Integer,Description="Number of no-called samples (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__NEGATIVE_TRAIN_SITE,Number=0,Type=Flag,Description="This variant was used to build the negative training set of bad variants (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__POSITIVE_TRAIN_SITE,Number=0,Type=Flag,Description="This variant was used to build the positive training set of good variants (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__QD,Number=1,Type=Float,Description="Variant Confidence/Quality by Depth (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__ReadPosRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read position bias (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__VQSLOD,Number=1,Type=Float,Description="Log odds ratio of being a true variant versus being false under the trained gaussian mixture model (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=EXAC__culprit,Number=1,Type=String,Description="The annotation which was the worst performing in the Gaussian mixture model, likely the reason why the variant was filtered out (from /anno/data/variantDBs/ExAC/ExAC.r0.3.1.sites.vep_norm.vcf.gz)">
##INFO=<ID=FS,Number=1,Type=Float,Description="Phred-scaled p-value using Fisher's exact test to detect strand bias">
##INFO=<ID=GNOMAD_EXOMES__AC,Number=A,Type=Integer,Description="Allele count in genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_AFR,Number=A,Type=Integer,Description="Allele count in African/African American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_AMR,Number=A,Type=Integer,Description="Allele count in Admixed American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_ASJ,Number=A,Type=Integer,Description="Allele count in Ashkenazi Jewish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_EAS,Number=A,Type=Integer,Description="Allele count in East Asian genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_FIN,Number=A,Type=Integer,Description="Allele count in Finnish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_Female,Number=A,Type=Integer,Description="Allele count in Female genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_Male,Number=A,Type=Integer,Description="Allele count in Male genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_NFE,Number=A,Type=Integer,Description="Allele count in Non-Finnish European genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_OTH,Number=A,Type=Integer,Description="Allele count in Other (population not assigned) genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AC_SAS,Number=A,Type=Integer,Description="Allele count in South Asian genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF,Number=A,Type=Float,Description="Allele Frequency among genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_AFR,Number=A,Type=Float,Description="Allele Frequency among African/African American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_AMR,Number=A,Type=Float,Description="Allele Frequency among Admixed American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_ASJ,Number=A,Type=Float,Description="Allele Frequency among Ashkenazi Jewish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_EAS,Number=A,Type=Float,Description="Allele Frequency among East Asian genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_FIN,Number=A,Type=Float,Description="Allele Frequency among Finnish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_Female,Number=A,Type=Float,Description="Allele Frequency among Female genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_Male,Number=A,Type=Float,Description="Allele Frequency among Male genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_NFE,Number=A,Type=Float,Description="Allele Frequency among Non-Finnish European genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_OTH,Number=A,Type=Float,Description="Allele Frequency among Other (population not assigned) genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AF_SAS,Number=A,Type=Float,Description="Allele Frequency among South Asian genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN,Number=1,Type=Integer,Description="Total number of alleles in called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_AFR,Number=1,Type=Integer,Description="Total number of alleles in African/African American called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_AMR,Number=1,Type=Integer,Description="Total number of alleles in Admixed American called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_ASJ,Number=1,Type=Integer,Description="Total number of alleles in Ashkenazi Jewish called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_EAS,Number=1,Type=Integer,Description="Total number of alleles in East Asian called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_FIN,Number=1,Type=Integer,Description="Total number of alleles in Finnish called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_Female,Number=1,Type=Integer,Description="Total number of alleles in Female called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_Male,Number=1,Type=Integer,Description="Total number of alleles in Male called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_NFE,Number=1,Type=Integer,Description="Total number of alleles in Non-Finnish European called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_OTH,Number=1,Type=Integer,Description="Total number of alleles in Other (population not assigned) called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AN_SAS,Number=1,Type=Integer,Description="Total number of alleles in South Asian called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AS_FilterStatus,Number=A,Type=String,Description="Random Forests filter status for each allele (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__AS_RF,Number=A,Type=Float,Description="Random Forests probability for each allele (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__BaseQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt Vs. Ref base qualities (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__ClippingRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref number of hard clipped bases (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__DB,Number=0,Type=Flag,Description="dbSNP Membership (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__DP,Number=1,Type=Integer,Description="Approximate read depth; some reads may have been filtered (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__FS,Number=1,Type=Float,Description="Phred-scaled p-value using Fisher's exact test to detect strand bias (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_AFR,Number=G,Type=Integer,Description="Count of African/African American individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_AMR,Number=G,Type=Integer,Description="Count of Admixed American individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_ASJ,Number=G,Type=Integer,Description="Count of Ashkenazi Jewish individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_EAS,Number=G,Type=Integer,Description="Count of East Asian individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_FIN,Number=G,Type=Integer,Description="Count of Finnish individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_Female,Number=G,Type=Integer,Description="Count of Female individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_Male,Number=G,Type=Integer,Description="Count of Male individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_NFE,Number=G,Type=Integer,Description="Count of Non-Finnish European individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_OTH,Number=G,Type=Integer,Description="Count of Other (population not assigned) individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__GC_SAS,Number=G,Type=Integer,Description="Count of South Asian individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_AFR,Number=A,Type=Integer,Description="Count of hemizygous African/African American individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_AMR,Number=A,Type=Integer,Description="Count of hemizygous Admixed American individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_ASJ,Number=A,Type=Integer,Description="Count of hemizygous Ashkenazi Jewish individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_EAS,Number=A,Type=Integer,Description="Count of hemizygous East Asian individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_FIN,Number=A,Type=Integer,Description="Count of hemizygous Finnish individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_NFE,Number=A,Type=Integer,Description="Count of hemizygous Non-Finnish European individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_OTH,Number=A,Type=Integer,Description="Count of hemizygous Other (population not assigned) individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__Hemi_SAS,Number=A,Type=Integer,Description="Count of hemizygous South Asian individuals (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__InbreedingCoeff,Number=1,Type=Float,Description="Inbreeding coefficient as estimated from the genotype likelihoods per-sample when compared against the Hardy-Weinberg expectation (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__MQ,Number=1,Type=Float,Description="RMS Mapping Quality (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__MQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read mapping qualities (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__QD,Number=1,Type=Float,Description="Variant Confidence/Quality by Depth (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_EXOMES__ReadPosRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read position bias (from /anno/data/variantDBs/gnomAD/gnomad.exomes.r2.0.1.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC,Number=A,Type=Integer,Description="Allele count in genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_AFR,Number=A,Type=Integer,Description="Allele count in African/African American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_AMR,Number=A,Type=Integer,Description="Allele count in Admixed American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_ASJ,Number=A,Type=Integer,Description="Allele count in Ashkenazi Jewish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_EAS,Number=A,Type=Integer,Description="Allele count in East Asian genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_FIN,Number=A,Type=Integer,Description="Allele count in Finnish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_Female,Number=A,Type=Integer,Description="Allele count in Female genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_Male,Number=A,Type=Integer,Description="Allele count in Male genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_NFE,Number=A,Type=Integer,Description="Allele count in Non-Finnish European genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_OTH,Number=A,Type=Integer,Description="Allele count in Other (population not assigned) genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AC_SAS,Number=1,Type=String,Description="calculated by first of overlapping values in field AC_SAS from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz">
##INFO=<ID=GNOMAD_GENOMES__AF,Number=A,Type=Float,Description="Allele Frequency among genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_AFR,Number=A,Type=Float,Description="Allele Frequency among African/African American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_AMR,Number=A,Type=Float,Description="Allele Frequency among Admixed American genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_ASJ,Number=A,Type=Float,Description="Allele Frequency among Ashkenazi Jewish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_EAS,Number=A,Type=Float,Description="Allele Frequency among East Asian genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_FIN,Number=A,Type=Float,Description="Allele Frequency among Finnish genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_Female,Number=A,Type=Float,Description="Allele Frequency among Female genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_Male,Number=A,Type=Float,Description="Allele Frequency among Male genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_NFE,Number=A,Type=Float,Description="Allele Frequency among Non-Finnish European genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_OTH,Number=A,Type=Float,Description="Allele Frequency among Other (population not assigned) genotypes, for each ALT allele, in the same order as listed (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AF_SAS,Number=1,Type=String,Description="calculated by first of overlapping values in field AF_SAS from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz">
##INFO=<ID=GNOMAD_GENOMES__AN,Number=1,Type=Integer,Description="Total number of alleles in called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_AFR,Number=1,Type=Integer,Description="Total number of alleles in African/African American called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_AMR,Number=1,Type=Integer,Description="Total number of alleles in Admixed American called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_ASJ,Number=1,Type=Integer,Description="Total number of alleles in Ashkenazi Jewish called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_EAS,Number=1,Type=Integer,Description="Total number of alleles in East Asian called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_FIN,Number=1,Type=Integer,Description="Total number of alleles in Finnish called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_Female,Number=1,Type=Integer,Description="Total number of alleles in Female called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_Male,Number=1,Type=Integer,Description="Total number of alleles in Male called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_NFE,Number=1,Type=Integer,Description="Total number of alleles in Non-Finnish European called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_OTH,Number=1,Type=Integer,Description="Total number of alleles in Other (population not assigned) called genotypes (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AN_SAS,Number=1,Type=String,Description="calculated by first of overlapping values in field AN_SAS from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz">
##INFO=<ID=GNOMAD_GENOMES__AS_FilterStatus,Number=A,Type=String,Description="Random Forests filter status for each allele (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__AS_RF,Number=A,Type=Float,Description="Random Forests probability for each allele (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__BaseQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt Vs. Ref base qualities (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__ClippingRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref number of hard clipped bases (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__DB,Number=0,Type=Flag,Description="dbSNP Membership (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__DP,Number=1,Type=Integer,Description="Approximate read depth; some reads may have been filtered (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__FS,Number=1,Type=Float,Description="Phred-scaled p-value using Fisher's exact test to detect strand bias (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_AFR,Number=G,Type=Integer,Description="Count of African/African American individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_AMR,Number=G,Type=Integer,Description="Count of Admixed American individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_ASJ,Number=G,Type=Integer,Description="Count of Ashkenazi Jewish individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_EAS,Number=G,Type=Integer,Description="Count of East Asian individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_FIN,Number=G,Type=Integer,Description="Count of Finnish individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_Female,Number=G,Type=Integer,Description="Count of Female individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_Male,Number=G,Type=Integer,Description="Count of Male individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_NFE,Number=G,Type=Integer,Description="Count of Non-Finnish European individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_OTH,Number=G,Type=Integer,Description="Count of Other (population not assigned) individuals for each genotype (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__GC_SAS,Number=1,Type=String,Description="calculated by first of overlapping values in field GC_SAS from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz">
##INFO=<ID=GNOMAD_GENOMES__Hom_AFR,Number=A,Type=Integer,Description="Count of homozygous African/African American individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_AMR,Number=A,Type=Integer,Description="Count of homozygous Admixed American individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_ASJ,Number=A,Type=Integer,Description="Count of homozygous Ashkenazi Jewish individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_EAS,Number=A,Type=Integer,Description="Count of homozygous East Asian individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_FIN,Number=A,Type=Integer,Description="Count of homozygous Finnish individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_Female,Number=A,Type=Integer,Description="Count of homozygous Female individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_Male,Number=A,Type=Integer,Description="Count of homozygous Male individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_NFE,Number=A,Type=Integer,Description="Count of homozygous Non-Finnish European individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_OTH,Number=A,Type=Integer,Description="Count of homozygous Other (population not assigned) individuals (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__Hom_SAS,Number=1,Type=String,Description="calculated by first of overlapping values in field Hom_SAS from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz">
##INFO=<ID=GNOMAD_GENOMES__InbreedingCoeff,Number=1,Type=Float,Description="Inbreeding coefficient as estimated from the genotype likelihoods per-sample when compared against the Hardy-Weinberg expectation (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__MQ,Number=1,Type=Float,Description="RMS Mapping Quality (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__MQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read mapping qualities (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__QD,Number=1,Type=Float,Description="Variant Confidence/Quality by Depth (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GNOMAD_GENOMES__ReadPosRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read position bias (from /anno/data/variantDBs/gnomAD/gnomad.genomes.r2.0.1.sliced.norm.vcf.gz)">
##INFO=<ID=GQ_MEAN,Number=1,Type=Float,Description="Mean of all GQ values">
##INFO=<ID=GQ_STDDEV,Number=1,Type=Float,Description="Standard deviation of all GQ values">
##INFO=<ID=HGMD__HGMD_type,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__acc_num,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__amino,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__author,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__base,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__chromosome,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__codon,Number=.,Type=Integer,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__comments,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__coordEND,Number=.,Type=Integer,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__coordSTART,Number=.,Type=Integer,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__deletion,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__disease,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__entrezID,Number=.,Type=Integer,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__extrarefs,Number=.,Type=String,Description="Format: (pmid|title|author|fullname|year|vol|issue|page|reftag|gene|disease|comments) (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__fullname,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__gene,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__hgvs,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__insertion,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__ivs,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__journal,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__location,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__locref,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__new_date,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__nucleotide,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__omimid,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__page,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__pmid,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__refCORE,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__refVER,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__score,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__strand,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__tag,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__type,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__vol,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__wildtype,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HGMD__year,Number=.,Type=String,Description="None (from /anno/data/variantDBs/HGMD/hgmd-2017.4_norm.vcf.gz)">
##INFO=<ID=HWP,Number=1,Type=Float,Description="P value from test of Hardy Weinberg Equilibrium">
##INFO=<ID=HaplotypeScore,Number=1,Type=Float,Description="Consistency of the site with at most two segregating haplotypes">
##INFO=<ID=InbreedingCoeff,Number=1,Type=Float,Description="Inbreeding coefficient as estimated from the genotype likelihoods per-sample when compared against the Hardy-Weinberg expectation">
##INFO=<ID=MLEAC,Number=A,Type=Integer,Description="Maximum likelihood expectation (MLE) for the allele counts (not necessarily the same as the AC), for each ALT allele, in the same order as listed">
##INFO=<ID=MLEAF,Number=A,Type=Float,Description="Maximum likelihood expectation (MLE) for the allele frequency (not necessarily the same as the AF), for each ALT allele, in the same order as listed">
##INFO=<ID=MQ,Number=1,Type=Float,Description="RMS Mapping Quality">
##INFO=<ID=MQ0,Number=1,Type=Integer,Description="Total Mapping Quality Zero Reads">
##INFO=<ID=MQRankSum,Number=1,Type=Float,Description="Z-score From Wilcoxon rank sum test of Alt vs. Ref read mapping qualities">
##INFO=<ID=NCC,Number=1,Type=Integer,Description="Number of no-called samples">
##INFO=<ID=NEGATIVE_TRAIN_SITE,Number=0,Type=Flag,Description="This variant was used to build the negative training set of bad variants">
##INFO=<ID=OLD_MULTIALLELIC,Number=1,Type=String,Description="Original chr:pos:ref:alt encoding">
##INFO=<ID=OLD_VARIANT,Number=.,Type=String,Description="Original chr:pos:ref:alt encoding">
##INFO=<ID=POSITIVE_TRAIN_SITE,Number=0,Type=Flag,Description="This variant was used to build the positive training set of good variants">
##INFO=<ID=QD,Number=1,Type=Float,Description="Variant Confidence/Quality by Depth">
##INFO=<ID=ReadPosRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read position bias">
##INFO=<ID=SOR,Number=1,Type=Float,Description="Symmetric Odds Ratio of 2x2 contingency table to detect strand bias">
##INFO=<ID=VQSLOD,Number=1,Type=Float,Description="Log odds ratio of being a true variant versus being false under the trained gaussian mixture model">
##INFO=<ID=culprit,Number=1,Type=String,Description="The annotation which was the worst performing in the Gaussian mixture model, likely the reason why the variant was filtered out">
##INFO=<ID=inDB__AC_OUST1,Number=A,Type=Integer,Description="Allele count. Number of observed alleles for given variant. (=2*Hom_OUST1+Het_OUST1)",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__AC_OUSWES,Number=A,Type=Integer,Description="Allele count. Number of observed alleles for given variant. (=2*Hom_OUSWES+Het_OUSWES)",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=inDB__AF_OUST1,Number=A,Type=Float,Description="Allele frequency (=AC_OUST1/AN_OUST1)",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__AF_OUSWES,Number=A,Type=Float,Description="Allele frequency (=AC_OUSWES/AN_OUSWES)",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=inDB__AN_OUST1,Number=1,Type=Integer,Description="Allele number. Total number of alleles on position (=2*SAMPLE_COUNT)",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__AN_OUSWES,Number=1,Type=Integer,Description="Allele number. Total number of alleles on position (=2*SAMPLE_COUNT)",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=inDB__Het_OUST1,Number=A,Type=Integer,Description="Number of observed heterozygotes for given variant",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__Het_OUSWES,Number=A,Type=Integer,Description="Number of observed heterozygotes for given variant",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=inDB__Hom_OUST1,Number=A,Type=Integer,Description="Number of observed homozygotes for given variant",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__Hom_OUSWES,Number=A,Type=Integer,Description="Number of observed homozygotes for given variant",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=inDB__filter_OUST1,Number=.,Type=String,Description="The FILTER field from in-house database",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__filter_OUSWES,Number=.,Type=String,Description="The FILTER field from in-house database",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=inDB__indications_OUST1,Number=.,Type=String,Description="Number of observed samples (note: not allele count) having this variant, given per indication.",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUST1-2017-06-15.vcf.gz)">
##INFO=<ID=inDB__indications_OUSWES,Number=.,Type=String,Description="Number of observed samples (note: not allele count) having this variant, given per indication.",Source="In-house database",Version="2.1 (from /anno/data/variantDBs/inDB/inDB-OUSWES-2017-06-14.vcf.gz)">
##INFO=<ID=pseudo_exon_ngs_dead_zone,Number=0,Type=Flag,Description="calculated by flag of overlapping values in column 2 from /anno/data/pseudogenes/gim.2016.58/Table_S1_List1_NGS_Dead_Zone_exon_level.bed.gz">
##INFO=<ID=pseudo_exon_ngs_problem_high,Number=0,Type=Flag,Description="calculated by flag of overlapping values in column 2 from /anno/data/pseudogenes/gim.2016.58/Table_S2_List2_NGS_Problem_List_High_Stringency_exon_level.bed.gz">
##INFO=<ID=pseudo_exon_ngs_problem_low,Number=0,Type=Flag,Description="calculated by flag of overlapping values in column 2 from /anno/data/pseudogenes/gim.2016.58/Table_S3_List3_NGS_Problem_List_Low_Stringency_exon_level.bed.gz">
##INFO=<ID=pseudo_gene_ngs_dead_zone,Number=0,Type=Flag,Description="calculated by flag of overlapping values in column 2 from /anno/data/pseudogenes/gim.2016.58/Table_S5_List1_NGS_Dead_Zone_gene_level.bed.gz">
##INFO=<ID=pseudo_gene_ngs_problem_high,Number=0,Type=Flag,Description="calculated by flag of overlapping values in column 2 from /anno/data/pseudogenes/gim.2016.58/Table_S7_List2_NGS_Problem_List_High_Stringency_gene_level.bed.gz">
##INFO=<ID=pseudo_gene_ngs_problem_low,Number=0,Type=Flag,Description="calculated by flag of overlapping values in column 2 from /anno/data/pseudogenes/gim.2016.58/Table_S9_List3_NGS_Problem_List_Low_Stringency_gene_level.bed.gz">
##INFO=<ID=set,Number=1,Type=String,Description="Source VCF for the merged record in CombineVariants">
##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths for the ref and alt alleles in the order listed">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Approximate read depth (reads with MQ=255 or with bad mates are filtered)">
##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=MIN_DP,Number=1,Type=Integer,Description="Minimum DP observed within the GVCF block">
##FORMAT=<ID=PGT,Number=1,Type=String,Description="Physical phasing haplotype information, describing how the alternate alleles are phased in relation to one another">
##FORMAT=<ID=PID,Number=1,Type=String,Description="Physical phasing ID information, where each unique ID within a given sample (but not across samples) connects records within a phasing group">
##FORMAT=<ID=PL,Number=G,Type=Integer,Description="Normalized, Phred-scaled likelihoods for genotypes as defined in the VCF specification">
##FORMAT=<ID=SB,Number=4,Type=Integer,Description="Per-sample component statistics which comprise the Fisher's Exact Test to detect strand bias.">
##ALT=<ID=NON_REF,Description="Represents any possible alternative allele at this location">
##GATKCommandLine=<ID=CombineVariants,Version=3.3-0-g37228af,Date="Thu May 10 03:33:14 CEST 2018",Epoch=1525915994045,CommandLineOptions="analysis_type=CombineVariants input_file=[] showFullBamList=false read_buffer_size=null phone_home=AWS gatk_key=null tag=NA read_filter=[] intervals=null excludeIntervals=null interval_set_rule=UNION interval_merging=ALL interval_padding=0 reference_sequence=/cluster/projects/p22/production/sw/vcpipe/vcpipe-bundle/genomic/gatkBundle_2.5/human_g1k_v37_decoy.fasta nonDeterministicRandomSeed=false disableDithering=false maxRuntime=-1 maxRuntimeUnits=MINUTES downsampling_type=BY_SAMPLE downsample_to_fraction=null downsample_to_coverage=1000 baq=OFF baqGapOpenPenalty=40.0 refactor_NDN_cigar_string=false fix_misencoded_quality_scores=false allow_potentially_misencoded_quality_scores=false useOriginalQualities=false defaultBaseQualities=-1 performanceLog=null BQSR=null quantize_quals=0 disable_indel_quals=false emit_original_quals=false preserve_qscores_less_than=6 globalQScorePrior=-1.0 validation_strictness=SILENT remove_program_records=false keep_program_records=false sample_rename_mapping_file=null unsafe=null disable_auto_index_creation_and_locking_when_reading_rods=false no_cmdline_in_header=false sites_only=false never_trim_vcf_format_field=false bcf=false bam_compression=null simplifyBAM=false disable_bam_indexing=false generate_md5=false num_threads=4 num_cpu_threads_per_data_thread=1 num_io_threads=0 monitorThreadEfficiency=false num_bam_file_handles=null read_group_black_list=null pedigree=[] pedigreeString=[] pedigreeValidationType=STRICT allow_intervals_with_unindexed_bam=false generateShadowBCF=false variant_index_type=DYNAMIC_SEEK variant_index_parameter=-1 logging_level=INFO log_to_file=null help=false version=false variant=[(RodBindingCollection [(RodBinding name=variant source=Diag-Excap113-HG002-PM-TrioPU-v04.snp.filter.vcf)]), (RodBindingCollection [(RodBinding name=variant2 source=Diag-Excap113-HG002-PM-TrioPU-v04.indel.filter.vcf)])] out=org.broadinstitute.gatk.engine.io.stubs.VariantContextWriterStub genotypemergeoption=UNSORTED filteredrecordsmergetype=KEEP_IF_ANY_UNFILTERED multipleallelesmergetype=BY_TYPE rod_priority_list=null printComplexMerges=false filteredAreUncalled=false minimalVCF=false excludeNonVariants=false setKey=set assumeIdenticalSamples=false minimumN=1 suppressCommandLineHeader=false mergeInfoWithMaxAC=false filter_reads_with_N_cigar=false filter_mismatching_base_and_quals=false filter_bases_not_stored=false">
##GATKCommandLine=<ID=GenotypeGVCFs,Version=3.3-0-g37228af,Date="Thu May 10 03:27:11 CEST 2018",Epoch=1525915631838,CommandLineOptions="analysis_type=GenotypeGVCFs input_file=[] showFullBamList=false read_buffer_size=null phone_home=AWS gatk_key=null tag=NA read_filter=[] intervals=null excludeIntervals=null interval_set_rule=UNION interval_merging=ALL interval_padding=0 reference_sequence=/cluster/projects/p22/production/sw/vcpipe/vcpipe-bundle/genomic/gatkBundle_2.5/human_g1k_v37_decoy.fasta nonDeterministicRandomSeed=false disableDithering=false maxRuntime=-1 maxRuntimeUnits=MINUTES downsampling_type=BY_SAMPLE downsample_to_fraction=null downsample_to_coverage=1000 baq=OFF baqGapOpenPenalty=40.0 refactor_NDN_cigar_string=false fix_misencoded_quality_scores=false allow_potentially_misencoded_quality_scores=false useOriginalQualities=false defaultBaseQualities=-1 performanceLog=null BQSR=null quantize_quals=0 disable_indel_quals=false emit_original_quals=false preserve_qscores_less_than=6 globalQScorePrior=-1.0 validation_strictness=SILENT remove_program_records=false keep_program_records=false sample_rename_mapping_file=null unsafe=null disable_auto_index_creation_and_locking_when_reading_rods=false no_cmdline_in_header=false sites_only=false never_trim_vcf_format_field=false bcf=false bam_compression=null simplifyBAM=false disable_bam_indexing=false generate_md5=false num_threads=6 num_cpu_threads_per_data_thread=1 num_io_threads=0 monitorThreadEfficiency=false num_bam_file_handles=null read_group_black_list=null pedigree=[/net/p01-c2io-nfs/projects/p22/production/analyses/Diag-Excap113-HG002-PM-TrioPU-v04/result/2018-05-09_16:39:02/data/Diag-Excap113-HG002-PM-TrioPU-v04.ped] pedigreeString=[] pedigreeValidationType=STRICT allow_intervals_with_unindexed_bam=false generateShadowBCF=false variant_index_type=DYNAMIC_SEEK variant_index_parameter=-1 logging_level=INFO log_to_file=null help=false version=false variant=[(RodBindingCollection [(RodBinding name=variant source=Diag-Excap113-HG002-PM.g.vcf)]), (RodBindingCollection [(RodBinding name=variant2 source=Diag-Excap113-HG004b-MK.g.vcf)]), (RodBindingCollection [(RodBinding name=variant3 source=Diag-Excap113-HG003-FM.g.vcf)])] out=org.broadinstitute.gatk.engine.io.stubs.VariantContextWriterStub includeNonVariantSites=false annotateNDA=false heterozygosity=0.001 indel_heterozygosity=1.25E-4 standard_min_confidence_threshold_for_calling=30.0 standard_min_confidence_threshold_for_emitting=30.0 max_alternate_alleles=6 input_prior=[] sample_ploidy=2 annotation=[InbreedingCoeff, FisherStrand, QualByDepth, ChromosomeCounts, GenotypeSummaries, StrandOddsRatio] dbsnp=(RodBinding name= source=UNBOUND) filter_reads_with_N_cigar=false filter_mismatching_base_and_quals=false filter_bases_not_stored=false">
##GVCFBlock=minGQ=0(inclusive),maxGQ=1(exclusive)
##source=SelectVariants
##VEP=v79 cache=/anno/data/VEP/cache/homo_sapiens_merged/79_GRCh37 db=.
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	{sample_names}"""

VCF_LINE_TEMPLATE = """{chromosome}	{pos}	CI101425	{ref}	{alt}	5000.0	PASS	{annotation}	GT:AD:DP:GQ:PL	{sample_data}"""
VCF_SAMPLE_TEMPLATE = """{GT}:{AD}:{DP}:{GQ}:{PL}"""
DEFAULT_ANNOTATION = "CSQ=A|frameshift_variant|HIGH|BRCA2|ENSG00000139618|Transcript|ENST00000380152|protein_coding|10/27||ENST00000380152.3:c.1233dupA|ENSP00000369497.3:p.Pro412ThrfsTer9|1465-1466|1232-1233|411|I/IX|ata/atAa|CI101425|1||1|HGNC|1101||CCDS9344.1|ENSP00000369497||||hmmpanther:PTHR11289&hmmpanther:PTHR11289:SF0&PIRSF_domain:PIRSF002397||||||||||||||||,A|frameshift_variant|HIGH|BRCA2|675|Transcript|NM_000059.3|protein_coding|10/27||NM_000059.3:c.1233dupA|NP_000050.2:p.Pro412ThrfsTer9|1459-1460|1232-1233|411|I/IX|ata/atAa|CI101425|1||1|||YES||NP_000050.2|rseq_mrna_nonmatch&rseq_cds_mismatch&rseq_ens_match_cds|||||||||||||||||||,A|frameshift_variant|HIGH|BRCA2|ENSG00000139618|Transcript|ENST00000530893|protein_coding|10/10||ENST00000530893.2:c.864dupA|ENSP00000435699.2:p.Pro289ThrfsTer9|1430-1431|863-864|288|I/IX|ata/atAa|CI101425|1||1|HGNC|1101|||ENSP00000435699||||hmmpanther:PTHR11289:SF0&hmmpanther:PTHR11289||||||||||||||||,A|frameshift_variant|HIGH|BRCA2|ENSG00000139618|Transcript|ENST00000544455|protein_coding|10/28||ENST00000544455.1:c.1233dupA|ENSP00000439902.1:p.Pro412ThrfsTer9|1459-1460|1232-1233|411|I/IX|ata/atAa|CI101425|1||1|HGNC|1101|YES|CCDS9344.1|ENSP00000439902||||hmmpanther:PTHR11289:SF0&hmmpanther:PTHR11289&PIRSF_domain:PIRSF002397||||||||||||||||;BIC__BRCA2__Accession_Number=3029;BIC__BRCA2__Exon=10;BIC__BRCA2__NT=1461;BIC__BRCA2__Codon=411;BIC__BRCA2__Base_Change=ins@#SPA;BIC__BRCA2__AA_Change=Stop@#SP420;BIC__BRCA2__Designation=1461insA;BIC__BRCA2__HGVS_cDNA=c.1233_1234insA;BIC__BRCA2__HGVS_Protein=p.Ile411_Pro412?fs;BIC__BRCA2__Genotype=-;BIC__BRCA2__dbSNP=rs80359270;BIC__BRCA2__Mutation_Type=F;BIC__BRCA2__Mutation_Effect=*;BIC__BRCA2__Clinically_Important=yes;BIC__BRCA2__Depositor=Myriad;BIC__BRCA2__Patient_Sample_Source=-;BIC__BRCA2__ID_Number=15434;BIC__BRCA2__Number_Reported=-;BIC__BRCA2__G_or_S=G;BIC__BRCA2__Detection_Method=DS;BIC__BRCA2__Proband_Tumor_Type=-;BIC__BRCA2__nChr=-;BIC__BRCA2__A=-;BIC__BRCA2__C=-;BIC__BRCA2__G=-;BIC__BRCA2__T=-;BIC__BRCA2__Reference=-;BIC__BRCA2__Contact_Person=clinresearch@myriad.com;BIC__BRCA2__Notes=-;BIC__BRCA2__Creation_Date=12-JUN-00;BIC__BRCA2__Ethnicity=-;BIC__BRCA2__Nationality=Central/Eastern@#SPEurope;BIC__BRCA2__Addition_Information=no;CLINVARJSON=7B226F7665726C617073223A5B5B223133222C223332393036383437222C225441434343435441545447222C2241434154225D5D2C227075626D656473223A5B223230313034353834225D2C2276617269616E745F6964223A35313038382C2272637673223A7B22534356303030313435383337223A7B22636C696E6963616C5F7369676E69666963616E63655F737461747573223A5B226E6F20617373657274696F6E2063726974657269612070726F7669646564225D2C224847565370223A5B5D2C2274726169746E616D6573223A5B224272656173742D6F76617269616E2063616E6365722C2066616D696C69616C2032225D2C227472616974735F6D656467656E5F6964223A5B224332363735353230225D2C2264627661724944223A5B5D2C2276617269616E745F6964223A5B5D2C22636C696E6963616C5F7369676E69666963616E63655F6465736372223A5B22506174686F67656E6963225D2C226C6173745F6576616C7561746564223A5B5D2C2272734944223A5B5D2C227472616974735F6F727068616E65745F6964223A5B5D2C227375626D6974746572223A5B224249432028425243413229225D2C227472616974735F6F6D696D5F6964223A5B5D7D2C22534356303030333236353231223A7B22636C696E6963616C5F7369676E69666963616E63655F737461747573223A5B2263726974657269612070726F76696465642C2073696E676C65207375626D6974746572225D2C224847565370223A5B5D2C2274726169746E616D6573223A5B5D2C227472616974735F6D656467656E5F6964223A5B5D2C2264627661724944223A5B5D2C2276617269616E745F6964223A5B5D2C22636C696E6963616C5F7369676E69666963616E63655F6465736372223A5B22506174686F67656E6963225D2C226C6173745F6576616C7561746564223A5B2230322F31302F32303135225D2C2272734944223A5B5D2C227472616974735F6F727068616E65745F6964223A5B5D2C227375626D6974746572223A5B2243494D4241225D2C227472616974735F6F6D696D5F6964223A5B22363132353535225D7D2C22534356303030303731373736223A7B22636C696E6963616C5F7369676E69666963616E63655F737461747573223A5B226E6F20617373657274696F6E2070726F7669646564225D2C224847565370223A5B5D2C2274726169746E616D6573223A5B2246616D696C69616C2063616E636572206F6620627265617374225D2C227472616974735F6D656467656E5F6964223A5B224330333436313533225D2C2264627661724944223A5B5D2C2276617269616E745F6964223A5B5D2C22636C696E6963616C5F7369676E69666963616E63655F6465736372223A5B226E6F742070726F7669646564225D2C226C6173745F6576616C7561746564223A5B2230312F30322F32303133225D2C2272734944223A5B5D2C227472616974735F6F727068616E65745F6964223A5B5D2C227375626D6974746572223A5B22496E76697461652C225D2C227472616974735F6F6D696D5F6964223A5B5D7D2C22524356303030313132383938223A7B22636C696E6963616C5F7369676E69666963616E63655F737461747573223A5B227265766965776564206279206578706572742070616E656C225D2C224847565370223A5B22702E50726F3431325468726673225D2C2274726169746E616D6573223A5B224272656173742D6F76617269616E2063616E6365722C2066616D696C69616C2032225D2C227472616974735F6D656467656E5F6964223A5B224332363735353230225D2C2264627661724944223A5B5D2C2276617269616E745F6964223A5B223531303838225D2C22636C696E6963616C5F7369676E69666963616E63655F6465736372223A5B22506174686F67656E6963225D2C226C6173745F6576616C7561746564223A5B2230382F30392F32303136225D2C2272734944223A5B223830333539323730225D2C227472616974735F6F727068616E65745F6964223A5B22313435225D2C227375626D6974746572223A5B5D2C227472616974735F6F6D696D5F6964223A5B22363132353535225D7D2C22524356303030303433373633223A7B22636C696E6963616C5F7369676E69666963616E63655F737461747573223A5B226E6F20617373657274696F6E2070726F7669646564225D2C224847565370223A5B22702E50726F3431325468726673225D2C2274726169746E616D6573223A5B2246616D696C69616C2063616E636572206F6620627265617374225D2C227472616974735F6D656467656E5F6964223A5B224330333436313533225D2C2264627661724944223A5B5D2C2276617269616E745F6964223A5B223531303838225D2C22636C696E6963616C5F7369676E69666963616E63655F6465736372223A5B226E6F742070726F7669646564225D2C226C6173745F6576616C7561746564223A5B2230312F30322F32303133225D2C2272734944223A5B223830333539323730225D2C227472616974735F6F727068616E65745F6964223A5B5D2C227375626D6974746572223A5B5D2C227472616974735F6F6D696D5F6964223A5B22313134343830225D7D2C22534356303030333030343130223A7B22636C696E6963616C5F7369676E69666963616E63655F737461747573223A5B227265766965776564206279206578706572742070616E656C225D2C224847565370223A5B5D2C2274726169746E616D6573223A5B5D2C227472616974735F6D656467656E5F6964223A5B5D2C2264627661724944223A5B5D2C2276617269616E745F6964223A5B5D2C22636C696E6963616C5F7369676E69666963616E63655F6465736372223A5B22506174686F67656E6963225D2C226C6173745F6576616C7561746564223A5B2230382F30392F32303136225D2C2272734944223A5B5D2C227472616974735F6F727068616E65745F6964223A5B5D2C227375626D6974746572223A5B22454E49474D41225D2C227472616974735F6F6D696D5F6964223A5B22363132353535225D7D7D2C2276617269616E745F6465736372697074696F6E223A227265766965776564206279206578706572742070616E656C227D;HGMD__HGMD_type=insertion;HGMD__acc_num=CI101425;HGMD__author=Borg;HGMD__chromosome=13;HGMD__codon=411;HGMD__comments=None;HGMD__coordEND=32906849;HGMD__coordSTART=32906848;HGMD__disease=Breast@#SPcancer;HGMD__entrezID=675;HGMD__fullname=Hum@#SPMutat;HGMD__gene=BRCA2;HGMD__hgvs=1233dupA;HGMD__insertion=GGAGAAA^ATAaCCCCTATTGC;HGMD__journal=HUM@#SPMUT;HGMD__new_date=2010-03-12;HGMD__nucleotide=1233;HGMD__omimid=600185;HGMD__page=E1200;HGMD__pmid=20104584;HGMD__refCORE=NM_000059;HGMD__refVER=3;HGMD__score=0;HGMD__strand=+;HGMD__tag=DM;HGMD__vol=31;HGMD__year=2010"


def create_vcf(variants, sample_names):
    """
    Create a fake vcf for use in testing.

    Annotation is optional, if provided it should be a list of strings with same
    length as variant
    """
    vcf_data = VCF_TEMPLATE.format(sample_names="\t".join(sample_names))
    for variant in variants:
        variant_data = dict(variant)
        sample_data = []
        for sample in variant_data.pop("samples"):
            sample_data.append(VCF_SAMPLE_TEMPLATE.format(**sample))
        variant_data["sample_data"] = "\t".join(sample_data)
        additional_annotation = ";".join(
            ["{}={}".format(k, v) for k, v in variant_data["annotation"].items()]
        )
        variant_data["annotation"] = DEFAULT_ANNOTATION
        if additional_annotation:
            variant_data["annotation"] = ";" + additional_annotation
        vcf_data += "\n" + VCF_LINE_TEMPLATE.format(**variant_data)

    return vcf_data


def v(chr, pos, ref, alt, samples=None):
    variant = {"chromosome": chr, "pos": pos, "ref": ref, "alt": alt}
    if samples:
        variant["samples"] = samples
    return variant


ALLELE_ALT = "T"


def gv(samples):
    global ALLELE_ALT
    ALLELE_ALT += "T"
    variant = {"chromosome": "5", "pos": 123, "ref": "A", "alt": ALLELE_ALT, "annotation": {}}
    variant["samples"] = samples
    return variant


def s(gt, ad, dp, gq, pl):
    return {"GT": gt, "AD": ad, "DP": dp, "GQ": gq, "PL": pl}


def s_gt(gt):
    """ When you don't care about extra sample data """
    return s(gt, "0, 100", "100", "99", "0,10,20")


@st.composite
def block_strategy(draw, samples):
    """
    Generates a multiallelic "block" for multiple samples.
    """

    # Genotypes that say something and are not just 'fillers'
    genotypes = ["0/1", "1/1", "0/0", "./.", "0|1", "1|0", "0|0", ".|."]
    multiallelic_genotypes = genotypes + ["1/.", "./1", "1|.", ".|1"]
    block = list()

    # Track whether the genotype for each sample.
    # If a sample has started a block ('1/.')
    # it will need to finish it later ('./1').
    # If it has "used up" it's genotype already, it cannot make a new one,
    # but has to insert '0/.' or '0/0.
    sample_genotype = dict()  # {sample_name1: '1/.', sample_name2: './1'}

    block_size = draw(st.integers(min_value=1, max_value=len(samples) * 2))
    for idx in range(block_size):
        block_samples = list()
        for sample in samples:
            if sample not in sample_genotype:
                # Get our base genotype
                if block_size == 1:
                    gt = draw(st.sampled_from(genotypes))
                else:
                    gt = draw(st.sampled_from(genotypes + ["1/.", "1|."]))
            else:
                # Multiallelic case
                # This is rather complex, we need to check what genotype
                # we picked for this sample and insert sensible
                # filler genotypes for the rest of the block

                if block_size > 1:
                    sample_gt = tuple(sample_genotype[sample][::2])
                    phasing = sample_genotype[sample][1]
                    # Block as been started and last round -> finish it
                    if sample_gt == ("1", ".") and idx == block_size - 1:
                        gt = (".", "1")
                    # Block has been started, not last round ->
                    # random pick of finishing it or null data
                    elif sample_gt == ("1", ".") and idx != block_size - 1:
                        # We cannot risk ending all samples with './1'
                        # when we're not on the record in the block
                        # since one sample needs to end the block
                        if (
                            len(
                                [
                                    a
                                    for a in list(sample_genotype.values())
                                    if tuple(a[::2]) == ("1", ".")
                                ]
                            )
                            > 1
                        ):
                            gt = draw(st.sampled_from([(".", "1"), (".", ".")]))
                        else:
                            gt = (".", ".")
                    # Already ended, cannot have more variants
                    elif sample_gt == (".", "1"):
                        gt = (".", ".")
                    # Heterozygous variant, will not have others (they are other positions)
                    elif sample_gt in [("0", "1"), ("1", "0")]:
                        gt = ("0", ".")
                    elif sample_gt == ("1", "1"):
                        gt = (".", ".")
                    elif sample_gt == ("0", "0"):
                        gt = ("0", "0")
                    # If no coverage on initial draw, keep giving no coverage
                    elif sample_gt == (".", "."):
                        gt = (".", ".")
                    else:
                        assert False, "Shouldn't happen: {}".format(sample_gt)

                    gt = phasing.join(gt)

            if gt in multiallelic_genotypes:
                # Don't overwrite original genotype with './.
                if sample not in sample_genotype or tuple(gt[::2]) != (".", "."):
                    sample_genotype[sample] = gt

            # Draw from a limited pool to avoid too many combinations
            block_samples.append(
                s(
                    gt,
                    # AD (nonsensical values as we don't take GT into account)
                    "{},{}".format(
                        draw(st.integers(min_value=0, max_value=4)),
                        draw(st.integers(min_value=100, max_value=104)),
                    ),
                    # DP
                    draw(st.integers(min_value=100, max_value=103)),
                    # GQ
                    draw(st.integers(min_value=90, max_value=93)),
                    # PL (nonsensical values as we don't take GT into account)
                    "{},{},{}".format(
                        draw(st.integers(min_value=0, max_value=4)),
                        draw(st.integers(min_value=50, max_value=54)),
                        draw(st.integers(min_value=100, max_value=104)),
                    ),
                )
            )
        # If we have a block, at least one sample must start with '1/.',
        # or it makes no sense
        if idx == 1 and block_size > 1:
            assume(any(a == "1/." for a in list(sample_genotype.values())))
        if block_size > 1 and idx == block_size - 1:
            assume(any(a == "./1" for a in list(sample_genotype.values())))

        block.append(block_samples)
    log.debug("Created block of size {} with {} samples".format(block_size, len(samples)))

    # Debug: Print GTs the block
    # for b in block:
    #    print([sa['GT'] for sa in b])

    return block


@st.composite
def pedigree_strategy(draw, sample_names):
    """
    Samples are implicitly: <proband>, <father>, <mother>, <sibling1>, ...
    """

    PED_LINE = "{fam}\t{sample}\t{father}\t{mother}\t{sex}\t{affected}\t{proband}"

    # For single sample, ped file isn't needed
    if len(sample_names) == 1:
        return None, {sample_names[0]: {"affected": "2", "proband": "1", "sex": None}}

    proband_sample = sample_names[0]
    father_sample = None
    mother_sample = None
    if len(sample_names) > 1:
        father_sample = sample_names[1]
    if len(sample_names) > 2:
        mother_sample = sample_names[2]

    ped_file = ""
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
            ped_file += PED_LINE.format(**ped_info) + "\n"
            ped_infos[sample_name] = ped_info

    return ped_file, ped_infos


@st.composite
def vcf_family_strategy(draw, max_num_samples):
    num_samples = draw(st.integers(min_value=1, max_value=max_num_samples))

    base_names = ["PROBAND", "FATHER", "MOTHER"]
    sample_names = base_names[:num_samples]

    if num_samples > 3:
        sample_names += ["SIBLING_{}".format(idx - 3) for idx in range(3, num_samples)]
    block = draw(block_strategy(sample_names))

    variants = [gv(s) for s in block]
    vcf = create_vcf(variants, sample_names)

    ped, ped_info = draw(pedigree_strategy(sample_names))
    meta = {"variants": variants, "sample_names": sample_names, "ped_info": ped_info}
    return vcf, ped, meta
