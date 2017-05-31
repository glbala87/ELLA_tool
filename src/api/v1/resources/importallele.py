from api.util.util import request_json, authenticate
from api.v1.resource import Resource
from vardb.datamodel import gene
from vardb.deposit import importers


class ImportAlleleList(Resource):

    @authenticate()
    @request_json(['allele', 'genepanel'], True)
    def post(self, session, data=None, user=None):
        """
        Imports alleles into the database and creates AlleleInterpretation objects
        if not existing, adding them to the list of alleles that needs interpretation.

        ---
        summary: Import alleles
        tags:
            - Import
        parameters:
          - name: data
            in: body
            required: true
            schema:
              title: allele list
              type: array
              description: List of allele data
              items:
                type: object
                required:
                  - allele
                  - genepanel
                properties:
                  allele:
                    description: allele data
                    type: object
                    required:
                      - vcf
                      - annotation
                    properties:
                      vcf:
                        type: object
                        required:
                          - CHROM
                          - POS
                          - REF
                          - ALT
                        properties:
                          CHROM:
                            type: string
                          REF:
                            type: string
                          ALT:
                            type: string
                          POS:
                            type: int
                      annotation:
                        type: object
                        description: Allele annotation
                  genepanel:
                    description: Genepanel identifier
                    type: object
                    required:
                      - name
                      - version
                    properties:
                      name:
                        type: string
                      version:
                        type: string
              example:
                - allele:
                    vcf:
                      ALT: A
                      POS: 32972760
                      REF: G
                      CHROM: '13'
                  annotation:
                    - references:
                      - sources:
                        - CLINVAR
                        source_info: {}
                        pubmed_id: 25741868
                      transcripts:
                      - hgnc_id: '25037'
                        strand: -1
                        in_last_exon: 'no'
                        transcript: ENST00000459716
                        is_canonical: false
                        symbol: N4BP2L1
                        dbsnp:
                        - rs28897762
                        consequences:
                        - downstream_gene_variant
                      - strand: -1
                        hgnc_id: '25037'
                        in_last_exon: 'no'
                        symbol: N4BP2L1
                        is_canonical: false
                        transcript: ENST00000380139
                        consequences:
                        - downstream_gene_variant
                        dbsnp:
                        - rs28897762
                      - consequences:
                        - downstream_gene_variant
                        in_last_exon: 'no'
                        dbsnp:
                        - rs28897762
                        symbol: N4BP2L1
                        strand: -1
                        is_canonical: false
                        transcript: XM_005266588.1
                      - HGVSp: NM_000059.3:c.10110G>A(p.=)
                        strand: 1
                        HGVSc: NM_000059.3:c.10110G>A
                        in_last_exon: 'yes'
                        exon: 27/27
                        symbol: BRCA2
                        codons: agG/agA
                        amino_acids: R
                        HGVSp_short: c.10110G>A(p.=)
                        is_canonical: true
                        transcript: NM_000059.3
                        consequences:
                        - synonymous_variant
                        HGVSc_short: c.10110G>A
                        dbsnp:
                        - rs28897762
                      - consequences:
                        - synonymous_variant
                        HGVSc_short: c.10110G>A
                        dbsnp:
                        - rs28897762
                        exon: 27/28
                        codons: agG/agA
                        symbol: BRCA2
                        HGVSp_short: c.10110G>A(p.=)
                        amino_acids: R
                        transcript: ENST00000544455
                        is_canonical: true
                        in_last_exon: 'no'
                        HGVSp: ENST00000544455.1:c.10110G>A(p.=)
                        strand: 1
                        HGVSc: ENST00000544455.1:c.10110G>A
                        hgnc_id: '1101'
                      - transcript: NM_052818.2
                        is_canonical: true
                        strand: -1
                        symbol: N4BP2L1
                        in_last_exon: 'no'
                        dbsnp:
                        - rs28897762
                        consequences:
                        - downstream_gene_variant
                      - consequences:
                        - downstream_gene_variant
                        dbsnp:
                        - rs28897762
                        in_last_exon: 'no'
                        symbol: N4BP2L1
                        strand: -1
                        is_canonical: false
                        transcript: NM_001079691.1
                      - in_last_exon: 'no'
                        hgnc_id: '25037'
                        strand: -1
                        dbsnp:
                        - rs28897762
                        consequences:
                        - downstream_gene_variant
                        transcript: ENST00000380130
                        is_canonical: true
                        symbol: N4BP2L1
                      - dbsnp:
                        - rs28897762
                        consequences:
                        - downstream_gene_variant
                        transcript: ENST00000533776
                        is_canonical: false
                        symbol: BRCA2
                        in_last_exon: 'no'
                        hgnc_id: '1101'
                        strand: 1
                      external:
                        CLINVAR:
                          variant_id: 51043
                          items:
                          - rcv: SCV000145753
                            variant_id: ''
                            last_evaluated: 12/06/2000
                            submitter: BIC (BRCA2)
                            traitnames: Breast-ovarian cancer, familial 2
                            clinical_significance_descr: Uncertain significance
                          - rcv: RCV000112841
                            clinical_significance_descr: Conflicting interpretations of pathogenicity
                            submitter: ''
                            last_evaluated: 03/11/2014
                            traitnames: Breast-ovarian cancer, familial 2
                            variant_id: '51043'
                          - variant_id: '51043'
                            last_evaluated: 14/06/2016
                            submitter: ''
                            traitnames: Fanconi anemia
                            clinical_significance_descr: Likely benign
                            rcv: RCV000260989
                          variant_description: criteria provided, conflicting interpretations
                      frequencies:
                        ExAC:
                          hom:
                            AFR: 0
                            EAS: 0
                            AMR: 0
                            G: 0
                            NFE: 0
                            SAS: 0
                            OTH: 0
                            FIN: 0
                          num:
                            EAS: 8650
                            AFR: 10328
                            AMR: 11522
                            G: 121148
                            NFE: 66640
                            FIN: 6612
                            OTH: 906
                            SAS: 16490
                          freq:
                            FIN: 0.00181488203266788
                            SAS: 0.00139478471801092
                            OTH: 0.0011037527593819
                            NFE: 0.00198079231692677
                            AMR: 0.000607533414337789
                            G: 0.00146927724766401
                            AFR: 0.000193648334624322
                            EAS: 0.000115606936416185
                          het:
                            AMR: 7
                            G: 178
                            AFR: 2
                            EAS: 1
                            OTH: 1
                            SAS: 23
                            FIN: 12
                            NFE: 132
                          count:
                            AMR: 7
                            G: 178
                            EAS: 1
                            AFR: 2
                            OTH: 1
                            SAS: 23
                            FIN: 12
                            NFE: 132
                        1000g:
                          freq:
                            EUR: 0.003
                            AFR: 0
                            EAS: 0
                            AMR: 0.0014
                            SAS: 0
                            G: 0.0008
                      prediction: {}



        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        for item in data:

            # Create or update allele + annotation
            allele_importer = importers.AlleleImporter(session)
            allele = allele_importer.process(item['allele']['vcf'])[0]

            annotation_importer = importers.AnnotationImporter(session)
            annotation_importer.create_or_update_annotation(
                session,
                allele,
                item['allele']['annotation']
            )

            # Create workflow object if it doesn't exist
            genepanel = session.query(gene.Genepanel).filter(
                gene.Genepanel.name == item['genepanel']['name'],
                gene.Genepanel.version == item['genepanel']['version']
            ).one()

            ali = importers.AlleleInterpretationImporter(session)
            ali.process(genepanel, allele.id)

        session.commit()

        return None
