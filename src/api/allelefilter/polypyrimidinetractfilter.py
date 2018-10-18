from sqlalchemy import or_, and_, tuple_, func, case
from vardb.datamodel import gene, allele


class PolypyrimidineTractFilter(object):

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, gp_allele_ids, filter_config):
        """
        Filter alleles in the polypyrimidine tract (defined as 3 to 20 bases upstream of exon start,
        strandedness taken into account)

        Only filter out alleles that are either SNPs from C->T, T->C, or deletions of
        C, T, CC, TT, CT, TC (strandedness taken into account)

        We do *not* filter out alleles where a deletion is flanked by A (positive strand)
        or G (negative strand), as this could create a new AG splice site. Ideally, we would check if
        the deletion was flanked by A on one side and G on another, but since we do not use a FASTA-file,
        we are unable to check both sides. The one side we do check comes from the vcf_ref-column in
        the allele-table
        """

        ppy_filtered = {}
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if not allele_ids:
                ppy_filtered[gp_key] = set()
                continue
            gp_genes = self.session.query(
                gene.Transcript.gene_id,
                gene.Gene.hgnc_symbol
            ).join(
                gene.Genepanel.transcripts
            ).join(
                gene.Gene
            ).filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version) == gp_key,
            )

            gp_gene_ids, gp_gene_symbols = zip(*[(g[0], g[1]) for g in gp_genes])

            ppy_tract_region = filter_config['ppy_tract_region']
            ppy_padding = abs(ppy_tract_region[0])


            # Extract transcripts associated with the genepanel
            # To potentially limit the number of regions we need to check, exclude transcripts where we have no alleles
            # overlapping in the region [tx_start-max_padding, tx_end+max_padding]. The filter clause in the query
            # should have no effect on the result, but is included only for performance

            genepanel_transcripts = self.session.query(
                gene.Transcript.id,
                gene.Transcript.gene_id,
                gene.Transcript.transcript_name,
                gene.Transcript.chromosome,
                gene.Transcript.strand,
                gene.Transcript.tx_start,
                gene.Transcript.tx_end,
                gene.Transcript.cds_start,
                gene.Transcript.cds_end,
                gene.Transcript.exon_starts,
                gene.Transcript.exon_ends,
            ).join(
                gene.genepanel_transcript,
                and_(
                    gene.genepanel_transcript.c.transcript_id == gene.Transcript.id,
                    tuple_(gene.genepanel_transcript.c.genepanel_name, gene.genepanel_transcript.c.genepanel_version) == gp_key
                )
            ).filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.chromosome == gene.Transcript.chromosome,
                or_(
                    and_(
                        allele.Allele.start_position >= gene.Transcript.tx_start-ppy_padding,
                        allele.Allele.start_position <= gene.Transcript.tx_end+ppy_padding,
                    ),
                    and_(
                        allele.Allele.open_end_position > gene.Transcript.tx_start-ppy_padding,
                        allele.Allele.open_end_position < gene.Transcript.tx_end+ppy_padding,
                    )
                )
            ).subquery()

            # Unwrap the exons for the genepanel transcript
            genepanel_transcript_exons = self.session.query(
                genepanel_transcripts.c.id,
                genepanel_transcripts.c.gene_id,
                genepanel_transcripts.c.chromosome,
                genepanel_transcripts.c.strand,
                genepanel_transcripts.c.cds_start,
                genepanel_transcripts.c.cds_end,
                func.unnest(genepanel_transcripts.c.exon_starts).label('exon_start'),
                func.unnest(genepanel_transcripts.c.exon_ends).label('exon_end'),
            )

            # query_print_table(genepanel_transcript_exons)

            genepanel_transcript_exons = genepanel_transcript_exons.subquery()


            # Regions with applied padding
            def _create_region(transcripts, region_start, region_end):
                return self.session.query(
                    transcripts.c.chromosome.label('chromosome'),
                    transcripts.c.strand.label('strand'),
                    region_start.label('region_start'),
                    region_end.label('region_end')
                ).distinct()

            # Upstream region for positive strand transcript is [exon_start+ppy_tract[0], exon_start+ppy_tract[1])
            # Upstream region for reverse strand transcript is (exon_end-ppy_tract_region[0], exon_end-exon_upstream-ppy_tract_region[1]]
            # Note: ppy_tract_region[0]/ppy_tract_region[1] is a *negative* number
            ppytract_start = case(
                [(genepanel_transcript_exons.c.strand == '-', genepanel_transcript_exons.c.exon_end-ppy_tract_region[1])],
                else_=genepanel_transcript_exons.c.exon_start + ppy_tract_region[0],
            )

            ppytract_end = case(
                [(genepanel_transcript_exons.c.strand == '-', genepanel_transcript_exons.c.exon_end-ppy_tract_region[0])],
                else_=genepanel_transcript_exons.c.exon_start + ppy_tract_region[1],
            )

            ppytract = _create_region(genepanel_transcript_exons, ppytract_start, ppytract_end)

            # query_print_table(ppytract)

            ppytract = ppytract.subquery()

            # Find allele ids within ppy tract region
            ppy_allele_ids = self.session.query(
                allele.Allele.id,
            ).filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.chromosome == ppytract.c.chromosome,
                # Check that the allele is within the polypyrimidine tract region
                or_(
                    and_(
                        allele.Allele.start_position >= ppytract.c.region_start,
                        allele.Allele.start_position <= ppytract.c.region_end,
                    ),
                    and_(
                        allele.Allele.open_end_position > ppytract.c.region_start,
                        allele.Allele.open_end_position < ppytract.c.region_end,
                    ),
                    and_(
                        allele.Allele.start_position <= ppytract.c.region_start,
                        allele.Allele.open_end_position > ppytract.c.region_end,
                    )
                ),
                # Check that the variant is a C/T SNP or deletion of C/T of length <= 2
                or_(
                    and_(
                        ppytract.c.strand == '+',
                        or_(
                            and_(
                                allele.Allele.change_type == 'del',
                                allele.Allele.change_from.in_(['C', 'T', 'CT', 'CC', 'TT', 'TC']),
                                allele.Allele.vcf_alt != 'A'
                            ),
                            and_(
                                allele.Allele.change_type == 'SNP',
                                allele.Allele.change_from.in_(['T', 'C']),
                                allele.Allele.change_to.in_(['T', 'C']),
                            )

                        )
                    ),
                    and_(
                        # On reverse strand, we substitute C/T with G/A
                        ppytract.c.strand == '-',
                        or_(
                            and_(
                                allele.Allele.change_type == 'del',
                                allele.Allele.change_from.in_(['G', 'A', 'GA', 'GG', 'AA', 'AG']),
                                allele.Allele.vcf_alt != 'G'
                            ),
                            and_(
                                allele.Allele.change_type == 'SNP',
                                allele.Allele.change_from.in_(['A', 'G']),
                                allele.Allele.change_to.in_(['A', 'G']),
                            )

                        )
                    )
                )
            )

            ppy_filtered[gp_key] = set([a[0] for a in ppy_allele_ids])

        return ppy_filtered
