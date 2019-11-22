from typing import Any, Dict, List, Optional, Set, Tuple, Union
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql.selectable import TableClause
from sqlalchemy import or_, and_, tuple_, func, case, Column, MetaData, Integer

from vardb.datamodel import gene, annotationshadow, allele
from api.util import queries


class RegionFilter(object):
    def __init__(self, session: Session, config: Optional[Dict[str, Any]]) -> None:
        self.session = session
        self.config = config

    def create_gene_padding_table(
        self, gene_ids: Tuple[int, int, int, int, int, int], filter_config: Dict[str, Any]
    ) -> Table:
        """
        Create a temporary table for the gene specific padding of the form
        ------------------------------------------------------------------------------------------------
        | hgnc_id | exon_upstream | exon_downstream | coding_region_upstream | coding_region_downstream |
        ------------------------------------------------------------------------------------------------
        | 26113   | -35           | 15              | -20                    | 20                       |
        | 28163   | -20           | 6               | -20                    | 20                       |
        | 2567    | -20           | 6               | -50                    | 50                       |

        Returns an ORM-representation of this table
        """

        splice_region = filter_config["splice_region"]
        utr_region = filter_config["utr_region"]
        values = []
        for gene_id in gene_ids:
            values.append(
                str((gene_id, splice_region[0], splice_region[1], utr_region[0], utr_region[1]))
            )

        self.session.execute("DROP TABLE IF EXISTS tmp_gene_padding;")
        self.session.execute(
            "CREATE TEMP TABLE tmp_gene_padding (hgnc_id Integer, exon_upstream Integer, exon_downstream Integer, coding_region_upstream Integer, coding_region_downstream Integer) ON COMMIT DROP;"
        )

        if values:
            self.session.execute("INSERT INTO tmp_gene_padding VALUES {};".format(",".join(values)))

        t = Table(
            "tmp_gene_padding",
            MetaData(),
            Column("hgnc_id", Integer()),
            Column("exon_upstream", Integer()),
            Column("exon_downstream", Integer()),
            Column("coding_region_upstream", Integer()),
            Column("coding_region_downstream", Integer()),
        )
        return t

    def create_genepanel_transcripts_table(
        self, gp_key: Tuple[str, str], allele_ids: List[int], max_padding: int
    ) -> TableClause:
        # Extract transcripts associated with the genepanel
        # To potentially limit the number of regions we need to check, exclude transcripts where we have no alleles
        # overlapping in the region [tx_start-max_padding, tx_end+max_padding]. The filter clause in the query
        # should have no effect on the result, but is included only for performance

        return (
            self.session.query(
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
            )
            .join(
                gene.genepanel_transcript,
                and_(
                    gene.genepanel_transcript.c.transcript_id == gene.Transcript.id,
                    tuple_(
                        gene.genepanel_transcript.c.genepanel_name,
                        gene.genepanel_transcript.c.genepanel_version,
                    )
                    == gp_key,
                ),
            )
            .filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.chromosome == gene.Transcript.chromosome,
                or_(
                    and_(
                        allele.Allele.start_position >= gene.Transcript.tx_start - max_padding,
                        allele.Allele.start_position <= gene.Transcript.tx_end - 1 + max_padding,
                    ),
                    and_(
                        allele.Allele.open_end_position - 1
                        > gene.Transcript.tx_start - max_padding,
                        allele.Allele.open_end_position < gene.Transcript.tx_end + max_padding,
                    ),
                ),
            )
            .temp_table("region_filter_internal_genepanel_transcripts")
        )

    def create_genepanel_transcript_exons_table(
        self, genepanel_transcripts: TableClause
    ) -> TableClause:

        # Unwrap the exons for the genepanel transcript
        return self.session.query(
            genepanel_transcripts.c.id,
            genepanel_transcripts.c.gene_id,
            genepanel_transcripts.c.chromosome,
            genepanel_transcripts.c.strand,
            genepanel_transcripts.c.cds_start,
            genepanel_transcripts.c.cds_end,
            func.unnest(genepanel_transcripts.c.exon_starts).label("exon_start"),
            func.unnest(genepanel_transcripts.c.exon_ends).label("exon_end"),
        ).temp_table("region_filter_internal")

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, Any]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
         Filter alleles outside regions of interest.
         Regions of interest are based on these criteria:
          - Coding region
          - Splice region
          - UTR region (upstream/downstream of coding start/coding end)

         These are all based on the transcript definition of the genepanel
         transcripts with genomic coordinates for
         - Transcript (tx) start and end
         - Coding region (cds) start and end
         - Exon start and end

         UTR regions are upstream/downstream of cds start/end, with padding specified in config
         Splice regions are upstream/downstream of exon start/end, with padding specified in config

           |          +--------------+------------+           +------------------------+             +-----------+-------+        |
           |----------+              |            +-----------+                        +-------------+           |       +--------|
           |          +--------------+------------+           +------------------------+             +-----------+-------+        |
          tx        exon           coding        exon        exon                     exon          exon       coding   exon     tx
          start     start          start         end         start                    end           start       end     end      end

        """

        region_filtered: Dict[Tuple[str, str], Set[int]] = {}
        for gp_key, allele_ids in gp_allele_ids.items():
            if not allele_ids:
                region_filtered[gp_key] = set()
                continue

            # Fetch all gene ids associated with the genepanel
            gp_genes = (
                self.session.query(gene.Transcript.gene_id, gene.Gene.hgnc_symbol)
                .join(gene.Genepanel.transcripts)
                .join(gene.Gene)
                .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == gp_key)
            )

            gp_gene_ids, gp_gene_symbols = list(zip(*[(g[0], g[1]) for g in gp_genes]))

            # Create temporary gene padding table for the genes in the genepanel
            tmp_gene_padding = self.create_gene_padding_table(gp_gene_ids, filter_config)

            max_padding = self.session.query(
                func.abs(func.max(tmp_gene_padding.c.exon_upstream)),
                func.abs(func.max(tmp_gene_padding.c.exon_downstream)),
                func.abs(func.max(tmp_gene_padding.c.coding_region_upstream)),
                func.abs(func.max(tmp_gene_padding.c.coding_region_downstream)),
            )
            max_padding = max(*max_padding.all())

            # Create temp tables
            genepanel_transcripts = self.create_genepanel_transcripts_table(
                gp_key, allele_ids, max_padding
            )
            genepanel_transcript_exons = self.create_genepanel_transcript_exons_table(
                genepanel_transcripts
            )

            # Create queries for
            # - Coding regions
            # - Upstream splice region
            # - Downstream splice region
            # - Upstream UTR region
            # - Downstream UTR region

            # Coding regions
            # The coding regions may start within an exon, and we truncate the exons where this is the case
            # For example, if an exon is defined by positions [10,20], but cds_start is 15, we include the region [15,20]
            # |          +--------------+------------+           +-------------+             +-----------+-------+        |
            # |----------+              cccccccccccccc-----------ccccccccccccccc-------------ccccccccccccc       +--------|
            # |          +--------------+------------+           +-------------+             +-----------+-------+        |
            coding_start = case(
                [
                    (
                        genepanel_transcript_exons.c.cds_start
                        > genepanel_transcript_exons.c.exon_start,
                        genepanel_transcript_exons.c.cds_start,
                    )
                ],
                else_=genepanel_transcript_exons.c.exon_start,
            )

            coding_end = case(
                [
                    (
                        genepanel_transcript_exons.c.cds_end
                        < genepanel_transcript_exons.c.exon_end,
                        genepanel_transcript_exons.c.cds_end - 1,
                    )
                ],
                else_=genepanel_transcript_exons.c.exon_end - 1,
            )

            transcript_coding_regions = self.session.query(
                genepanel_transcript_exons.c.chromosome.label("chromosome"),
                coding_start.label("region_start"),
                coding_end.label("region_end"),
            ).filter(
                # Exclude exons outside the coding region
                genepanel_transcript_exons.c.exon_start < genepanel_transcript_exons.c.cds_end,
                genepanel_transcript_exons.c.exon_end > genepanel_transcript_exons.c.cds_start,
            )

            # Regions with applied padding
            def _create_region(transcripts, region_start, region_end):
                return (
                    self.session.query(
                        transcripts.c.chromosome.label("chromosome"),
                        region_start.label("region_start"),
                        region_end.label("region_end"),
                    )
                    .join(tmp_gene_padding, tmp_gene_padding.c.hgnc_id == transcripts.c.gene_id)
                    .filter(region_end > region_start)
                    .distinct()
                )

            # Splicing upstream
            # Include region upstream of the exon (not including exon starts or ends)

            # Transcript on positive strand:
            # |          +--------------+------------+           +-----------------+             +-----------+-------+        |
            # |-------iii+              |            +--------iii+                 +----------iii+           |       +--------|
            # |          +--------------+------------+           +-----------------+             +-----------+-------+        |
            # Transcript on reverse strand:
            # |          +--------------+------------+           +-----------------+             +-----------+-------+        |
            # |----------+              |            +iii--------+                 +iii----------+           |       +iii-----|
            # |          +--------------+------------+           +-----------------+             +-----------+-------+        |

            # Upstream region for positive strand transcript is [exon_start+exon_upstream, exon_start)
            # Downstream region for reverse strand transcript is (exon_end, exon_end-exon_upstream]
            # Note: exon_upstream is a *negative* number
            splicing_upstream_start = case(
                [
                    (
                        genepanel_transcript_exons.c.strand == "-",
                        genepanel_transcript_exons.c.exon_end,
                    )
                ],
                else_=genepanel_transcript_exons.c.exon_start + tmp_gene_padding.c.exon_upstream,
            )

            splicing_upstream_end = case(
                [
                    (
                        genepanel_transcript_exons.c.strand == "-",
                        genepanel_transcript_exons.c.exon_end
                        - 1
                        - tmp_gene_padding.c.exon_upstream,
                    )
                ],
                else_=genepanel_transcript_exons.c.exon_start - 1,
            )

            splicing_region_upstream = _create_region(
                genepanel_transcript_exons, splicing_upstream_start, splicing_upstream_end
            )

            # Splicing downstream
            # Include region downstream of the exon (not including exon starts or ends)
            # Transcript on positive strand:
            # |          +--------------+------------+           +----------------+             +-----------+-------+        |
            # |----------+              |            +ii---------+                +ii-----------+           |       +ii------|
            # |          +--------------+------------+           +----------------+             +-----------+-------+        |
            # Transcript on reverse strand:
            # |          +--------------+------------+           +----------------+             +-----------+-------+        |
            # |--------ii+              |            +---------ii+                +-----------ii+           |       +--------|
            # |          +--------------+------------+           +----------------+             +-----------+-------+        |

            # Downstream region for positive strand transcript is (exon_end, exon_end+exon_downstream]
            # Downstream region for reverse strand transcript is [exon_start-exon_downstream, exon_start)
            splicing_downstream_start = case(
                [
                    (
                        genepanel_transcript_exons.c.strand == "-",
                        genepanel_transcript_exons.c.exon_start
                        - tmp_gene_padding.c.exon_downstream,
                    )
                ],
                else_=genepanel_transcript_exons.c.exon_end,
            )

            splicing_downstream_end = case(
                [
                    (
                        genepanel_transcript_exons.c.strand == "-",
                        genepanel_transcript_exons.c.exon_start - 1,
                    )
                ],
                else_=genepanel_transcript_exons.c.exon_end
                - 1
                + tmp_gene_padding.c.exon_downstream,
            )

            splicing_region_downstream = _create_region(
                genepanel_transcript_exons, splicing_downstream_start, splicing_downstream_end
            )

            # UTR upstream
            # Do not include cds_start or cds_end, as these are not in the UTR
            # Transcript on positive strand:
            # |          +--------------+------------+           +---------------+             +-----------+-------+        |
            # |----------+          uuuu|            +-----------+               +-------------+           |       +--------|
            # |          +--------------+------------+           +---------------+             +-----------+-------+        |
            # Transcript on reverse strand:
            # |          +--------------+------------+           +---------------+             +-----------+-------+        |
            # |----------+              |            +-----------+               +-------------+           |uuuu   +--------|
            # |          +--------------+------------+           +---------------+             +-----------+-------+        |

            # UTR upstream region for positive strand transcript is (cds_start, cds_start+coding_region_upstream]
            # UTR upstream region for reverse strand transcript is [cds_end-coding_region_upstream, cds_end)
            utr_upstream_start = case(
                [(genepanel_transcripts.c.strand == "-", genepanel_transcripts.c.cds_end)],
                else_=genepanel_transcripts.c.cds_start + tmp_gene_padding.c.coding_region_upstream,
            )

            utr_upstream_end = case(
                [
                    (
                        genepanel_transcripts.c.strand == "-",
                        genepanel_transcripts.c.cds_end
                        - 1
                        - tmp_gene_padding.c.coding_region_upstream,
                    )
                ],
                else_=genepanel_transcripts.c.cds_start - 1,
            )

            utr_region_upstream = _create_region(
                genepanel_transcripts, utr_upstream_start, utr_upstream_end
            )

            # UTR downstream
            # Do not include cds_start or cds_end, as these are not in the UTR
            # Transcript on positive strand:
            # |          +--------------+------------+           +--------------+             +-----------+-------+        |
            # |----------+              |            +-----------+              +-------------+           |uuuu   +--------|
            # |          +--------------+------------+           +--------------+             +-----------+-------+        |
            # Transcript on reverse strand:
            # |          +--------------+------------+           +--------------+             +-----------+-------+        |
            # |----------+          uuuu|            +-----------+              +-------------+           |       +--------|
            # |          +--------------+------------+           +--------------+             +-----------+-------+        |

            # UTR downstream region for positive strand transcript is (cds_end, cds_end-coding_region_downstream]
            # UTR downstream region for reverse strand transcript is [cds_start+coding_region_downstream, cds_start)
            utr_downstream_start = case(
                [
                    (
                        genepanel_transcripts.c.strand == "-",
                        genepanel_transcripts.c.cds_start
                        - tmp_gene_padding.c.coding_region_downstream,
                    )
                ],
                else_=genepanel_transcripts.c.cds_end,
            )

            utr_downstream_end = case(
                [(genepanel_transcripts.c.strand == "-", genepanel_transcripts.c.cds_start - 1)],
                else_=genepanel_transcripts.c.cds_end
                - 1
                + tmp_gene_padding.c.coding_region_downstream,
            )
            utr_region_downstream = _create_region(
                genepanel_transcripts, utr_downstream_start, utr_downstream_end
            )

            # Union all regions together
            # |          +--------------+------------+           +-------------+             +-----------+-------+        |
            # |-------iii+          uuuuccccccccccccccii---------cccccccccccccccii--------iiicccccccccccccuuuu   +ii------|
            # |          +--------------+------------+           +-------------+             +-----------+-------+        |
            all_regions = (
                transcript_coding_regions.union(
                    splicing_region_upstream,
                    splicing_region_downstream,
                    utr_region_upstream,
                    utr_region_downstream,
                )
                .subquery()
                .alias("all_regions")
            )

            # Find allele ids within genomic region

            # In the database, insertions are stored with open_end_position=start_position + <length of insertion> + 1
            # This does not apply for region filtering, as we compare to the reference genome, where the insertion should have no length
            # TODO: Change datamodel to use open_end_position=start_position+1 for insertions
            open_end_position = case(
                [(allele.Allele.change_type == "ins", allele.Allele.start_position + 1)],
                else_=allele.Allele.open_end_position,
            )

            allele_ids_in_genomic_region = self.session.query(allele.Allele.id).filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.chromosome == all_regions.c.chromosome,
                or_(
                    # Contained within or overlapping region
                    and_(
                        allele.Allele.start_position >= all_regions.c.region_start,
                        allele.Allele.start_position <= all_regions.c.region_end,
                    ),
                    and_(
                        open_end_position > all_regions.c.region_start,
                        open_end_position <= all_regions.c.region_end,
                    ),
                    # Region contained within variant
                    and_(
                        allele.Allele.start_position <= all_regions.c.region_start,
                        open_end_position > all_regions.c.region_end,
                    ),
                ),
            )

            allele_ids_in_genomic_region = [a[0] for a in allele_ids_in_genomic_region]
            allele_ids_outside_region = set(allele_ids) - set(allele_ids_in_genomic_region)

            # Discard the next filters if there are no variants left to filter on
            if not allele_ids_outside_region:
                region_filtered[gp_key] = set()
                continue

            #
            # Save alleles based on computed HGVSc distance
            #
            # We look at computed exon_distance/coding_region_distance from annotation
            # on transcripts present in the genepanel (disregarding version number)
            # For alleles with computed distance within splice_region or utr_region,
            # they will not be filtered out
            # This can happen when there is a mismatch between genomic position and annotated HGVSc.
            # Observed for alleles in repeated regions: In the imported VCF,
            # the alleles are left aligned. VEP left aligns w.r.t. *transcript direction*,
            # and therefore, there could be a mismatch in position
            # See for example
            # https://variantvalidator.org/variantvalidation/?variant=NM_020366.3%3Ac.907-16_907-14delAAT&primary_assembly=GRCh37&alignment=splign
            annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
                self.session, [gp_key], allele_ids
            ).subquery()

            allele_ids_in_hgvsc_region = (
                self.session.query(
                    annotationshadow.AnnotationShadowTranscript.allele_id,
                    annotationshadow.AnnotationShadowTranscript.transcript,
                    annotationshadow.AnnotationShadowTranscript.hgvsc,
                    annotationshadow.AnnotationShadowTranscript.exon_distance,
                    annotationshadow.AnnotationShadowTranscript.coding_region_distance,
                    tmp_gene_padding.c.exon_upstream,
                    tmp_gene_padding.c.exon_downstream,
                    tmp_gene_padding.c.coding_region_upstream,
                    tmp_gene_padding.c.coding_region_downstream,
                )
                .join(
                    # Join in transcripts used in annotation
                    # Note: The annotation_transcripts_genepanel only contains transcripts
                    # matching transcripts in the genepanel.
                    # Therefore, we are sure that we only filter here on genepanel
                    # transcripts (disregarding version number)
                    annotation_transcripts_genepanel,
                    and_(
                        annotation_transcripts_genepanel.c.annotation_transcript
                        == annotationshadow.AnnotationShadowTranscript.transcript,
                        annotation_transcripts_genepanel.c.allele_id
                        == annotationshadow.AnnotationShadowTranscript.allele_id,
                    ),
                )
                .join(
                    # Join in gene padding table, to use gene specific padding
                    tmp_gene_padding,
                    tmp_gene_padding.c.hgnc_id
                    == annotation_transcripts_genepanel.c.genepanel_hgnc_id,
                )
                .filter(
                    annotationshadow.AnnotationShadowTranscript.allele_id.in_(
                        allele_ids_outside_region
                    ),
                    annotationshadow.AnnotationShadowTranscript.exon_distance
                    >= tmp_gene_padding.c.exon_upstream,
                    annotationshadow.AnnotationShadowTranscript.exon_distance
                    <= tmp_gene_padding.c.exon_downstream,
                    or_(
                        # We do not save exonic UTR alleles if they are
                        # outside [coding_region_upstream, coding_region_downstream]
                        # For coding exonic variant, the coding_region_distance is None
                        annotationshadow.AnnotationShadowTranscript.coding_region_distance.is_(
                            None
                        ),
                        and_(
                            annotationshadow.AnnotationShadowTranscript.coding_region_distance
                            >= tmp_gene_padding.c.coding_region_upstream,
                            annotationshadow.AnnotationShadowTranscript.coding_region_distance
                            <= tmp_gene_padding.c.coding_region_downstream,
                        ),
                    ),
                )
            )

            allele_ids_in_hgvsc_region = set([a[0] for a in allele_ids_in_hgvsc_region])
            allele_ids_outside_region -= allele_ids_in_hgvsc_region

            # Discard the next filter if there are no variants left to filter on
            if not allele_ids_outside_region:
                region_filtered[gp_key] = set()
                continue

            region_filtered[gp_key] = allele_ids_outside_region

        return region_filtered
