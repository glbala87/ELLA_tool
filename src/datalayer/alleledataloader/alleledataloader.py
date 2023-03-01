import json
from collections import defaultdict
from typing import Dict, List

from sqlalchemy import and_, case, func, or_, text, tuple_
from sqlalchemy.orm import aliased

from api.config import config

# TODO: This import should be refactored somehow, reaching into the api is weird.
from api.schemas import (
    AlleleAssessmentSchema,
    AlleleReportSchema,
    AlleleSchema,
    AnnotationSchema,
    CustomAnnotationSchema,
    GenotypeSampleDataSchema,
    GenotypeSchema,
    ReferenceAssessmentSchema,
    SampleSchema,
)
from datalayer import queries
from datalayer.alleledataloader.annotationprocessor import AnnotationProcessor
from datalayer.alleledataloader.calculate_qc import genotype_calculate_qc
from datalayer.allelefilter.genotypetable import get_genotype_temp_table
from datalayer.allelefilter.segregationfilter import SegregationFilter
from vardb.datamodel import allele, annotationshadow, gene, genotype, sample
from vardb.datamodel.annotation import Annotation, CustomAnnotation
from vardb.datamodel.assessment import AlleleAssessment, AlleleReport, ReferenceAssessment

# Top level keys:
KEY_REFERENCE_ASSESSMENTS = "reference_assessments"
KEY_ALLELE_ASSESSMENT = "allele_assessment"
KEY_ALLELE_REPORT = "allele_report"
KEY_CUSTOM_ANNOTATION = "custom_annotation"
KEY_ANNOTATION = "annotation"
KEY_GENOTYPE = "genotype"
KEY_SAMPLES = "samples"
KEY_ALLELE = "allele"

KEY_ANNOTATIONS = "annotations"


SEGREGATION_TAGS = [
    "denovo",
    "parental_mosaicism",
    "compound_heterozygous",
    "autosomal_recessive_homozygous",
    "xlinked_recessive_homozygous",
]


class Warnings(object):
    def __init__(self, session, alleles, genepanel=None, analysis_id=None):
        self.session = session
        self.alleles = alleles
        self.allele_ids = [al["id"] for al in alleles]
        self.analysis_id = analysis_id
        if genepanel:
            self.gp_key = (genepanel.name, genepanel.version)
        else:
            self.gp_key = None

    def get_warnings(self):
        allele_id_warnings = defaultdict(dict)
        nearby_warnings = self._check_nearby()
        for aid in nearby_warnings:
            allele_id_warnings[aid]["nearby_allele"] = nearby_warnings[aid]

        worse_consequence = self._check_worse_consequence()
        for aid in worse_consequence:
            allele_id_warnings[aid]["worse_consequence"] = worse_consequence[aid]

        return allele_id_warnings

    def _check_nearby(self):
        # Sort all alleles in analysis by chromosome, start, and end_position, then create "frames" to check our
        # alleles against.
        #
        # The frames are create for each allele, and encompasses all subsequent alleles
        # where the start_position is within 3bp of the frame allele's open_end_position (and they are on same chromosome).
        #
        # We check all positions in the frame against the frame allele's position for nearby.
        # What we check are:
        # 1. <frame allele start> - <subsequent allele start>
        # 2. <frame allele end> - <subsequent allele start>
        # 3. <frame allele end> - <subsequent allele end>
        #
        # Note 1: We do not need to check start_end, because the alleles are sorted by start_position. Therefore, start_start
        # is *always* smaller than start_end.
        #
        # Note 2: This implementation does not check specifically for overlaps.
        # E.g.: The alleles 1-1-100 and 1-49-50 (chrom, start, end) will not trigger warning
        # FIXME: This should be a simple implementation, but requires some improved testing
        #
        # The implementation should be O(N*m) where N is the total number of alleles and m is the frame size.
        #
        # Illustration:
        #
        # Consider the following alleles (all on same chromosome for simplicity). Asterisk denotes alleles of interest.
        #
        #         Id  Start   End
        #         1*    1       2
        #         2     1       7
        #         3*    4      10
        #
        # This will create two frames:
        #
        # Frame 1:
        #         Id  Start   End
        #         1*    1       2  <-- Frame allele
        #         2     1       7  <-- Subsequent allele
        #         3*    5      10  <-- Subsequent allele
        #
        # Here, warnings will be created for allele id 1 (nearby allele 2 and 3) and 3 (nearby allele 1)
        #
        # Frame 2:
        #         Id  Start   End
        #         2     1       7  <-- Frame allele
        #         3*    4      10  <-- Subsequent allele
        #
        # Here, a warning will be created for allele 3 (nearby allele 2)
        #
        # Warnings will not be created for allele 2 since this is not an allele of interest

        analysis_allele_ids = (
            self.session.query(allele.Allele.id)
            .join(genotype.Genotype.alleles, sample.Sample)
            .filter(sample.Sample.analysis_id == self.analysis_id)
        )

        alleles_ordered = (
            self.session.query(
                allele.Allele.id,
                allele.Allele.chromosome,
                allele.Allele.start_position,
                allele.Allele.open_end_position,
            )
            .order_by(
                allele.Allele.chromosome,
                allele.Allele.start_position,
                allele.Allele.open_end_position,
            )
            .filter(allele.Allele.id.in_(analysis_allele_ids))
            .all()
        )

        nearby_warnings = dict()

        # Create frames for alleles
        for i, (allele_id, chrom, start, end) in enumerate(alleles_ordered):
            # Loop over the subsequent alleles in frame
            j = i
            while j < len(alleles_ordered) - 1:
                j += 1
                other_allele_id, other_chrom, other_start, other_end = alleles_ordered[j]

                # Break if the next allele starts too far downstream
                if other_start - end > 3 or other_chrom != chrom:
                    break

                start_start = abs(other_start - start)
                end_start = abs(end - other_start)
                end_end = abs(end - other_end)

                if start_start < 3 or end_start < 3 or end_end < 3:
                    if allele_id in self.allele_ids:
                        nearby_warnings[
                            allele_id
                        ] = "Another variant is within 2 bp of this variant"

                    # Since the frames are created for subsequent alleles only, we need to set warning for other_allele
                    # here if the allele is in our alleles of interest
                    if other_allele_id in self.allele_ids:
                        nearby_warnings[
                            other_allele_id
                        ] = "Another variant is within 2 bp of this variant"

        return nearby_warnings

    def _check_worse_consequence(self):
        worse_consequence_warnings = dict()
        for al in self.alleles:
            if al["caller_type"] == "cnv":
                continue

            # Worse consequence
            worst_consequence = al.get("annotation", {}).get("worst_consequence", [])
            filtered_transcripts = al.get("annotation", {}).get("filtered_transcripts", [])
            if worst_consequence and not set(worst_consequence) & set(filtered_transcripts):
                consequences = dict()
                for w in worst_consequence:
                    transcript_data = next(
                        t for t in al["annotation"]["transcripts"] if t["transcript"] == w
                    )
                    consequences[w] = ",".join(transcript_data["consequences"])
                worse_consequence_warnings[al["id"]] = "Worse consequences found in: {}".format(
                    ", ".join(["{} ({})".format(k, v) for k, v in consequences.items()])
                )

        return worse_consequence_warnings


class AlleleDataLoader(object):
    def __init__(self, session):
        self.session = session
        self.inclusion_regex = config.get("transcripts", {}).get("inclusion_regex")
        self.segregation_filter = SegregationFilter(session, config)

    def _get_segregation_results(self, allele_ids, analysis_id, filterconfig_id):
        filter_config = (
            self.session.query(sample.FilterConfig)
            .filter(sample.FilterConfig.id == filterconfig_id)
            .one()
        )

        segregation_config = [
            fc for fc in filter_config.filterconfig["filters"] if fc["name"] == "segregation"
        ]
        if len(segregation_config) > 1:
            raise RuntimeError("Multiple segregation filters not supported")
        elif len(segregation_config) == 0:
            return None

        # Prior to schema version 2, the segregation config was not explicit.
        # Therefore, if schema < 2, use implicit config
        if filter_config.schema_version >= 2:
            segregation_config = segregation_config[0]["config"]
        else:
            segregation_config = {
                "no_coverage_parents": {"enable": False},
                "denovo": {"enable": True},
                "parental_mosaicism": {"enable": True},
                "compound_heterozygous": {"enable": True},
                "recessive_homozygous": {"enable": True},
            }

        segregation_results = self.segregation_filter.get_segregation_results(
            {analysis_id: allele_ids}, segregation_config
        )
        return segregation_results.get(analysis_id)

    def get_tags(self, allele_data, analysis_id=None, segregation_results=None):
        allele_ids_tags = defaultdict(set)

        for al in allele_data:
            # Has references
            if al.get("annotation", {}).get("references"):
                allele_ids_tags[al["id"]].add("has_references")

        if analysis_id:
            for al in allele_data:
                allele_id = al["id"]
                # Homozygous
                proband_samples = [s for s in al["samples"] if s["proband"]]
                if any(s["genotype"]["type"] == "Homozygous" for s in proband_samples):
                    allele_ids_tags[allele_id].add("homozygous")

                keys = ["qual", "pass", "dp", "allele_ratio"]
                for s in al["samples"]:
                    verification_checks = s["genotype"]["needs_verification_checks"]
                    if (
                        any(not v for k, v in verification_checks.items() if k in keys)
                        and verification_checks["hts"]
                    ):
                        allele_ids_tags[allele_id].add("low_quality")
                        break

                if segregation_results:
                    for tag in SEGREGATION_TAGS:
                        if allele_id in segregation_results[tag]:
                            allele_ids_tags[allele_id].add(tag)

        return allele_ids_tags

    def get_formatted_genotypes(self, allele_ids, sample_id):
        """
        Returns a dict of genotype id and formatted genotypes.

        Examples: 'A/G', 'A/ATT' (ins), 'AAT/-' (del), 'A/?' (missing allele info)

        This is ridiculously more complicated that one would first imagine...

        :note: Since we do not store alleles for non-proband samples on multiallelic
               sites (unless they match the proband's), they're given as '?'
        """

        allele_query = (
            self.session.query(
                genotype.Genotype.id,
                genotype.GenotypeSampleData.type,
                genotype.GenotypeSampleData.multiallelic,
                genotype.GenotypeSampleData.copy_number,
                allele.Allele.change_from,
                allele.Allele.change_to,
                allele.Allele.change_type,
                allele.Allele.length,
                allele.Allele.caller_type,
            )
            .join(
                genotype.GenotypeSampleData,
                and_(
                    genotype.Genotype.id == genotype.GenotypeSampleData.genotype_id,
                    genotype.GenotypeSampleData.secondallele.is_(False),
                    genotype.GenotypeSampleData.sample_id == sample_id,
                ),
            )
            .join(allele.Allele, allele.Allele.id == genotype.Genotype.allele_id)
            .filter(
                or_(
                    genotype.Genotype.allele_id.in_(allele_ids),
                    genotype.Genotype.secondallele_id.in_(allele_ids),
                )
            )
        )
        allele_query = allele_query.subquery()

        secondallele_query = (
            self.session.query(
                genotype.Genotype.id,
                genotype.GenotypeSampleData.type.label("second_type"),
                genotype.GenotypeSampleData.multiallelic.label("second_multiallelic"),
                genotype.GenotypeSampleData.copy_number.label("second_copy_number"),
                allele.Allele.change_from.label("second_change_from"),
                allele.Allele.change_to.label("second_change_to"),
                allele.Allele.change_type.label("second_change_type"),
                allele.Allele.length.label("second_length"),
                allele.Allele.caller_type.label("second_caller_type"),
            )
            .join(
                genotype.GenotypeSampleData,
                and_(
                    genotype.Genotype.id == genotype.GenotypeSampleData.genotype_id,
                    genotype.GenotypeSampleData.secondallele.is_(True),
                    genotype.GenotypeSampleData.sample_id == sample_id,
                ),
            )
            .join(allele.Allele, allele.Allele.id == genotype.Genotype.secondallele_id)
            .filter(
                or_(
                    genotype.Genotype.allele_id.in_(allele_ids),
                    genotype.Genotype.secondallele_id.in_(allele_ids),
                )
            )
        )
        secondallele_query = secondallele_query.subquery()

        genotype_query = self.session.query(
            allele_query.c.id,
            allele_query.c.type,
            allele_query.c.multiallelic,
            allele_query.c.change_from,
            allele_query.c.change_to,
            allele_query.c.change_type,
            allele_query.c.length,
            allele_query.c.caller_type,
            allele_query.c.copy_number,
            secondallele_query.c.second_type,
            secondallele_query.c.second_multiallelic,
            secondallele_query.c.second_change_from,
            secondallele_query.c.second_change_to,
            secondallele_query.c.second_change_type,
            secondallele_query.c.second_length,
            secondallele_query.c.second_caller_type,
            secondallele_query.c.second_copy_number,
        ).outerjoin(secondallele_query, allele_query.c.id == secondallele_query.c.id)

        genotype_candidates = genotype_query.all()

        genotype_id_formatted = dict()
        for g in genotype_candidates:
            gt1 = gt2 = None
            if g.caller_type == "cnv":
                assert g.second_change_type is None

                # TODO: Fix import
                # g.change_from = ""
                # g.change_to = ""

                # TODO: Fix length display, e.g. 12245 -> 12knt
                length_display = f"{g.length}nt"

                if g.change_type == "del" and g.type == "Heterozygous":
                    genotype_id_formatted[g.id] = f"({length_display})/-"
                elif g.change_type == "del" and g.type == "Homozygous":
                    genotype_id_formatted[g.id] = "-/-"
                elif g.change_type == "dup":
                    cn = g.copy_number if g.copy_number is not None else "?"
                    genotype_id_formatted[g.id] = f"CN: {cn} ({length_display})"
                elif g.change_type == "dup_tandem" and g.type == "Heterozygous":
                    genotype_id_formatted[g.id] = f"-/{length_display}"
                elif g.change_type == "dup_tandem" and g.type == "Homozygous":
                    genotype_id_formatted[g.id] = f"{length_display}/{length_display}"
                else:
                    raise RuntimeError(
                        f"Unhandled genotype: {g.caller_type} - {g.change_type} - {g.type}"
                    )
            else:
                if g.type == "No coverage":
                    gt1 = gt2 = "."
                    genotype_id_formatted[g.id] = "/".join([gt1, gt2])
                    continue

                if g.type == "Homozygous":
                    gt1 = gt2 = g.change_to or "-"
                    genotype_id_formatted[g.id] = "/".join([gt1, gt2])
                    continue

                if g.second_type == "Homozygous":
                    gt1 = gt2 = g.second_change_to or "-"
                    genotype_id_formatted[g.id] = "/".join([gt1, gt2])
                    continue

                # Many of these cases concern when the sample is not the proband,
                # and we're lacking some data.
                # If proband has secondallele, it must be heterozygous on both,
                # anything else doesn't make sense.
                # Note: multiallelic is True if there was a '.' in the genotype in vcf

                # If not multiallelic we can take the type at face value
                if not g.multiallelic:
                    if g.type == "Heterozygous":
                        gt1 = g.change_from or "-"
                        gt2 = g.change_to or "-"
                    elif g.type == "Reference":
                        gt1 = gt2 = g.change_from or "-"

                elif g.second_multiallelic is not None and not g.second_multiallelic:
                    if g.second_type == "Heterozygous":
                        gt1 = g.second_change_from or "-"
                        gt2 = g.second_change_to or "-"
                    elif g.second_type == "Reference":
                        gt1 = gt2 = g.second_change_from or "-"

                # If one or two are multiallelic, things gets a bit murkier
                else:
                    if not g.second_type:
                        if g.type == "Heterozygous":
                            # Multiallelic, but no secondallele -> no data for one allele
                            gt1 = g.change_to or "-"
                            gt2 = "?"
                        elif g.type == "Reference":
                            # We cannot know whether we have one or no reference, so both are unknown.
                            # This should very rarely happen
                            gt1 = gt2 = "?"
                    else:
                        # Most of these are non-proband cases
                        if g.second_type == "Heterozygous":
                            # Check whether we have the other allele stored in db
                            if g.type == "Heterozygous":
                                gt1 = g.change_to or "-"
                                gt2 = g.second_change_to or "-"
                            elif g.type == "Reference":
                                gt1 = g.second_change_to or "-"
                                gt2 = "?"
                        elif g.second_type == "Reference":
                            if g.type == "Heterozygous":
                                gt1 = g.change_to or "-"
                                gt2 = "?"
                            elif g.type == "Reference":
                                gt1 = "?"
                                gt2 = "?"

                assert gt1 is not None and gt2 is not None
                genotype_id_formatted[g.id] = "/".join([gt1, gt2])

        return genotype_id_formatted

    def get_p_denovo(self, allele_ids, analysis_id):
        family_ids = self.segregation_filter.get_family_ids(analysis_id)

        if len(family_ids) != 1:
            return dict()

        sample_ids = self.segregation_filter.get_family_sample_ids(analysis_id, family_ids[0])
        proband_sample = self.segregation_filter.get_proband_sample(analysis_id, family_ids[0])
        father_sample = self.segregation_filter.get_father_sample(proband_sample)
        mother_sample = self.segregation_filter.get_mother_sample(proband_sample)

        genotype_table = get_genotype_temp_table(
            self.session,
            allele_ids,
            sample_ids,
            genotypesampledata_extras={"gl": "genotype_likelihood"},
        )
        return self.segregation_filter.denovo_p_value(
            allele_ids, genotype_table, proband_sample.id, father_sample.id, mother_sample.id
        )

    def _load_sample_data(self, alleles, analysis_id, segregation_results):
        allele_ids = [al["id"] for al in alleles]
        genotype_schema = GenotypeSchema()
        sample_schema = SampleSchema()

        allele_ids_sample_data = defaultdict(list)

        # Load probands and groups families if available
        samples = (
            self.session.query(sample.Sample).filter(sample.Sample.analysis_id == analysis_id).all()
        )

        proband_samples = [s for s in samples if s.proband]

        proband_sample_id_family = defaultdict(dict)
        # Load parents and siblings
        for proband_sample in proband_samples:
            if proband_sample.father_id:
                father_sample = next(s for s in samples if s.id == proband_sample.father_id)
                proband_sample_id_family[proband_sample.id]["father"] = father_sample
            if proband_sample.mother_id:
                mother_sample = next(s for s in samples if s.id == proband_sample.mother_id)
                proband_sample_id_family[proband_sample.id]["mother"] = mother_sample

            sibling_samples = [s for s in samples if s.sibling_id == proband_sample.id]
            proband_sample_id_family[proband_sample.id]["siblings"] = sibling_samples

        genotypes = (
            self.session.query(genotype.Genotype)
            .filter(
                genotype.Genotype.sample_id.in_([p.id for p in proband_samples]),
                or_(
                    genotype.Genotype.allele_id.in_(allele_ids),
                    genotype.Genotype.secondallele_id.in_(allele_ids),
                ),
            )
            .all()
        )

        genotypesampledata = (
            self.session.query(genotype.GenotypeSampleData)
            .filter(
                genotype.GenotypeSampleData.sample_id.in_([s.id for s in samples]),
                genotype.GenotypeSampleData.genotype_id.in_([g.id for g in genotypes]),
            )
            .all()
        )

        sample_id_formatted_genotypes = dict()
        for s in samples:
            # Calculate the actual genotype for display (e.g. A/C or G/GTT)
            sample_id_formatted_genotypes[s.id] = self.get_formatted_genotypes(allele_ids, s.id)

        allele_ids_p_denovo = dict()
        if segregation_results:
            denovo_allele_ids = segregation_results.get("denovo", set())
            allele_ids_p_denovo = self.get_p_denovo(denovo_allele_ids, analysis_id)

        def load_sample_data(
            allele_data, sample, genotype, genotypesampledata, genotype_id_formatted, p_denovo=None
        ):
            is_secondallele = bool(genotype.secondallele_id == allele_data["id"])
            sample_data = sample_schema.dump(sample).data
            genotype_data = genotype_schema.dump(genotype).data
            gsd = next(
                g
                for g in genotypesampledata
                if g.sample_id == sample.id
                and g.secondallele == is_secondallele
                and g.genotype_id == gt.id
            )
            genotype_data.update(GenotypeSampleDataSchema().dump(gsd).data)
            genotype_data.update(
                genotype_calculate_qc(allele_data, genotype_data, sample_data["sample_type"])
            )
            genotype_data["formatted"] = genotype_id_formatted[genotype.id]
            if p_denovo:
                genotype_data["p_denovo"] = p_denovo

            sample_data[KEY_GENOTYPE] = genotype_data
            return sample_data

        # Create sample data with genotype for each allele
        for allele_data in alleles:
            allele_id_sample_data = list()
            for proband_sample in proband_samples:
                gt = next(
                    (
                        g
                        for g in genotypes
                        if (
                            g.allele_id == allele_data["id"]
                            or g.secondallele_id == allele_data["id"]
                        )
                        and g.sample_id == proband_sample.id
                    ),
                    None,
                )
                # Not all samples will share all alleles.
                # If there's not genotype, this sample doesn't have this allele
                if gt is None:
                    continue
                proband_sample_data = load_sample_data(
                    allele_data,
                    proband_sample,
                    gt,
                    genotypesampledata,
                    sample_id_formatted_genotypes[proband_sample.id],
                    allele_ids_p_denovo.get(allele_data["id"]),
                )
                proband_family_samples = proband_sample_id_family[proband_sample.id]
                if proband_family_samples.get("father"):
                    proband_sample_data["father"] = load_sample_data(
                        allele_data,
                        proband_family_samples["father"],
                        gt,
                        genotypesampledata,
                        sample_id_formatted_genotypes[proband_family_samples["father"].id],
                    )
                if proband_family_samples.get("mother"):
                    proband_sample_data["mother"] = load_sample_data(
                        allele_data,
                        proband_family_samples["mother"],
                        gt,
                        genotypesampledata,
                        sample_id_formatted_genotypes[proband_family_samples["mother"].id],
                    )
                if proband_family_samples.get("siblings"):
                    sibling_sample_data = list()
                    for sibling_sample in proband_family_samples["siblings"]:
                        sibling_sample_data.append(
                            load_sample_data(
                                allele_data,
                                sibling_sample,
                                gt,
                                genotypesampledata,
                                sample_id_formatted_genotypes[sibling_sample.id],
                            )
                        )
                    proband_sample_data["siblings"] = sibling_sample_data
                allele_id_sample_data.append(proband_sample_data)

            allele_ids_sample_data[allele_data["id"]] = allele_id_sample_data

        return allele_ids_sample_data

    def from_objs(
        self,
        alleles,
        link_filter=None,
        genepanel=None,  # Make genepanel mandatory?
        analysis_id=None,
        filterconfig_id=None,
        include_annotation=True,
        include_custom_annotation=True,
        include_allele_assessment=True,
        include_reference_assessments=True,
        include_allele_report=True,
        allele_assessment_schema=None,
    ) -> List[Dict]:
        """
        Loads data for a list of alleles from the database, and returns a dictionary
        with the final data, loaded using the allele schema.

        By default the most recent linked entities of the alleles are fetched from database.
        If specific entity ids are given in 'link_filter' those are loaded instead. Any explicitly given entities
        not linked to the alleles will not be part of the returned result

        Annotation is automatically processed using annotationprocessor. If possible, provide
        a genepanel for automatic transcript selection.

        If an analysis_id is provided, samples with genotypes will be included.
        Some tags also depend on having an analysis.

        :param alleles: List of allele objects.
        :param link_filter: a struct defining the ids of related entities to fetch. See other parameters for more info.
        :param analysis_id: Analysis id for including samples and genotype data.
        :param filterconfig_id: Filterconfig id to use for segregation tagging
        :param genepanel: Genepanel to be used in annotationprocessor.
        :type genepanel: vardb.datamodel.gene.Genepanel
        :param annotation: If true, load the ones mentioned in link_filter.annotation_id
        :param include_custom_annotation: If true, load the ones mentioned in link_filter.customannotation_id or, if not provided, the latest data
        :param include_allele_assessment: If true, load the ones mentioned in link_filter.alleleassessment_id or, if not provided, the latest data
        :param include_reference_assessments: If true, load the ones mentioned in link_filter.referenceassessment_id or, if not provided, the latest data
        :param include_allele_report: If true, load the ones mentioned in link_filter.allelereport_id or, if not provided, the latest data
        :param allele_assessment_schema: Use this schema for serialization. If None, use default
        :returns: dict with converted data using schema data.
        """

        # Load data and group into a temporary dictionary for internal usage
        # It will look like this in the end ({...} means data loaded using schema):
        # {
        #    id1: {
        #       'allele': {...},
        #       'genotype': {...} or not present,
        #       'annotation': {...} or not present,
        #       'custom_annotation': {...} or not present,
        #       'allele_assessment': {...} or not present,
        #       'reference_assessment': {...} or not present,
        #       'allele_report': {...} or not present
        #    },
        #    id2: ...
        # }

        allele_schema = AlleleSchema()

        accumulated_allele_data = dict()
        allele_ids = list()  # To keep input order

        for al in alleles:
            accumulated_allele_data[al.id] = {KEY_ALLELE: allele_schema.dump(al).data}
            allele_ids.append(al.id)

        segregation_results = None
        if analysis_id and allele_ids:
            if filterconfig_id is not None:
                segregation_results = self._get_segregation_results(
                    allele_ids, analysis_id, filterconfig_id
                )
            allele_id_sample_data = self._load_sample_data(
                [a["allele"] for a in list(accumulated_allele_data.values())],
                analysis_id,
                segregation_results,
            )
            for allele_id, sample_data in allele_id_sample_data.items():
                accumulated_allele_data[allele_id][KEY_SAMPLES] = sample_data

        allele_annotations, annotation_ids = list(), None
        if include_annotation:
            annotation_filters, annotation_ids = self.setup_entity_filter(
                Annotation, "annotation_id", allele_ids, link_filter
            )
            if annotation_filters:
                allele_annotations = (
                    self.session.query(Annotation).filter(*annotation_filters).all()
                )

        allele_custom_annotations = list()
        if include_custom_annotation:
            custom_annotation_filters, _ = self.setup_entity_filter(
                CustomAnnotation, "customannotation_id", allele_ids, link_filter
            )
            if custom_annotation_filters:
                allele_custom_annotations = (
                    self.session.query(CustomAnnotation).filter(*custom_annotation_filters).all()
                )

        allele_assessments = list()
        if include_allele_assessment:
            assessment_filters, _ = self.setup_entity_filter(
                AlleleAssessment, "alleleassessment_id", allele_ids, link_filter
            )
            if assessment_filters:
                allele_assessments = (
                    self.session.query(AlleleAssessment).filter(*assessment_filters).all()
                )

        reference_assessments = list()
        if include_reference_assessments:
            reference_filters, _ = self.setup_entity_filter(
                ReferenceAssessment, "referenceassessment_id", allele_ids, link_filter
            )
            if reference_filters:
                reference_assessments = (
                    self.session.query(ReferenceAssessment).filter(*reference_filters).all()
                )

        allele_reports = list()
        if include_allele_report:
            report_filters, _ = self.setup_entity_filter(
                AlleleReport, "allelereport_id", allele_ids, link_filter
            )
            if report_filters:
                allele_reports = self.session.query(AlleleReport).filter(*report_filters).all()

        # serialize the found entities:
        self.dump(
            accumulated_allele_data,
            allele_ids,
            allele_annotations,
            AnnotationSchema(),
            KEY_ANNOTATION,
        )
        self.dump(
            accumulated_allele_data,
            allele_ids,
            allele_custom_annotations,
            CustomAnnotationSchema(),
            KEY_CUSTOM_ANNOTATION,
        )
        self.dump(
            accumulated_allele_data,
            allele_ids,
            allele_assessments,
            allele_assessment_schema() if allele_assessment_schema else AlleleAssessmentSchema(),
            KEY_ALLELE_ASSESSMENT,
        )
        self.dump(
            accumulated_allele_data,
            allele_ids,
            reference_assessments,
            ReferenceAssessmentSchema(),
            KEY_REFERENCE_ASSESSMENTS,
            use_list=True,
        )
        self.dump(
            accumulated_allele_data,
            allele_ids,
            allele_reports,
            AlleleReportSchema(),
            KEY_ALLELE_REPORT,
        )

        # Create final data

        # If genepanel is provided, get annotation transcripts filtered on genepanel
        annotation_transcripts = None
        if genepanel:
            # sometimes we need to limit the amount of annotation data to load
            annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
                self.session,
                [(genepanel.name, genepanel.version)],
                annotation_ids=annotation_ids,
            ).subquery()

            annotation_transcripts = (
                self.session.query(
                    annotation_transcripts_genepanel.c.allele_id,
                    annotation_transcripts_genepanel.c.annotation_transcript,
                )
                .filter(annotation_transcripts_genepanel.c.allele_id.in_(allele_ids))
                .all()
            )

        inclusion_regex_filtered = None
        if self.inclusion_regex:
            inclusion_regex_filtered = (
                self.session.query(
                    annotationshadow.AnnotationShadowTranscript.allele_id,
                    annotationshadow.AnnotationShadowTranscript.transcript,
                )
                .filter(
                    annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids)
                    if allele_ids
                    else False,
                    text("transcript ~ :reg").params(reg=self.inclusion_regex),
                )
                .distinct()
                .all()
            )

        final_alleles = list()
        for allele_id in allele_ids:
            data = accumulated_allele_data[allele_id]
            final_allele = data[KEY_ALLELE]
            for key in [
                KEY_SAMPLES,
                KEY_ALLELE_ASSESSMENT,
                KEY_REFERENCE_ASSESSMENTS,
                KEY_ALLELE_REPORT,
            ]:
                if key in data:
                    final_allele[key] = data[key]

            if KEY_ANNOTATION in data:
                # Copy data to avoid mutating db object.
                # json -> much faster than copy.deepcopy
                annotation_data = json.loads(json.dumps(data[KEY_ANNOTATION][KEY_ANNOTATIONS]))

                # Clean up transcripts in annotation data
                # - Make sure to include all transcripts we have in our genepanel
                # - If a regex filter is given, filter out the ones not matching
                # - If we end up with an empty inclusion list, keep the original data (better with any data than nothing)
                transcripts_in_genepanel = set()
                if "transcripts" in annotation_data:
                    # 'filtered_transcripts' -> transcripts in our genepanel
                    if annotation_transcripts:
                        transcripts_in_genepanel = set(
                            [
                                a.annotation_transcript
                                for a in annotation_transcripts
                                if a.allele_id == allele_id
                            ]
                        )

                    # Filter main transcript list on inclusion regex
                    inclusion_transcripts = set()
                    if inclusion_regex_filtered:
                        inclusion_transcripts = set(
                            [t[1] for t in inclusion_regex_filtered if t[0] == allele_id]
                        )

                    to_include_transcripts = transcripts_in_genepanel | inclusion_transcripts
                    if to_include_transcripts:
                        annotation_data["transcripts"] = [
                            t
                            for t in annotation_data["transcripts"]
                            if t["transcript"] in to_include_transcripts
                        ]

                # Convert annotation using annotationprocessor
                processed_annotation = AnnotationProcessor.process(
                    annotation_data,
                    custom_annotation=data.get(KEY_CUSTOM_ANNOTATION, {}).get(KEY_ANNOTATIONS),
                    genepanel=genepanel,
                )
                final_allele[KEY_ANNOTATION] = processed_annotation

                final_allele[KEY_ANNOTATION]["filtered_transcripts"] = sorted(
                    list(transcripts_in_genepanel)
                )
                final_allele[KEY_ANNOTATION]["annotation_id"] = data[KEY_ANNOTATION]["id"]
                final_allele[KEY_ANNOTATION]["schema_version"] = data[KEY_ANNOTATION][
                    "schema_version"
                ]
                final_allele[KEY_ANNOTATION]["annotation_config_id"] = data[KEY_ANNOTATION][
                    "annotation_config_id"
                ]
                if KEY_CUSTOM_ANNOTATION in data:
                    final_allele[KEY_ANNOTATION]["custom_annotation_id"] = data[
                        KEY_CUSTOM_ANNOTATION
                    ]["id"]

            final_alleles.append(final_allele)

        allele_ids_tags = self.get_tags(
            final_alleles, analysis_id=analysis_id, segregation_results=segregation_results
        )
        allele_ids_warnings = Warnings(
            self.session, final_alleles, genepanel=genepanel, analysis_id=analysis_id
        ).get_warnings()

        for allele_id in allele_ids:
            final_allele = next(f for f in final_alleles if f["id"] == allele_id)
            final_allele["tags"] = sorted(list(allele_ids_tags.get(allele_id, [])))

        for allele_id, warnings in allele_ids_warnings.items():
            final_allele = next(f for f in final_alleles if f["id"] == allele_id)
            final_allele["warnings"] = warnings

        return final_alleles

    def dump(self, accumulator, allowed_allele_ids, items, schema, key, use_list=False):
        """

        :param allowed_allele_ids:
        :param accumulator: The dict to mutate with dumped data
        :param items:
        :param schema: the Schema to use for serializing
        :param key: the key in acc to place the dumped data
        :param use_list: the dumped values are appended to a list
        :return:

        """
        for item in items:
            if item.allele_id not in allowed_allele_ids:
                continue
            if use_list:
                if key not in accumulator[item.allele_id]:
                    accumulator[item.allele_id][key] = list()
                accumulator[item.allele_id][key].append(schema.dump(item, None).data)
            else:
                accumulator[item.allele_id][key] = schema.dump(item, None).data

    def setup_entity_filter(self, entity_clazz, key, allele_ids, query_object):
        """
        Create a list of filters for finding entities having a relationship
        with Allele. If the IDs of the entities are not defined in the query object,
        we choose the most recent ones instead of loading the specific ones.

        If query_object is given  we retrieve the entities mentioned there, regardless of there relationship
        with the allele mentioned in allele_ids. If an entity is not related to our alleles, they are discarded anyway
        when stitching together the final response

        :param entity_clazz: The entity to find
        :param key: the key of the query_object where the ids are found
        :param allele_ids: The IDs of Allele the entity class is related to
        :param query_object: a dict with ids of the entities to retrieve
        :return: An array of filters to be used in a session.query
        """
        filters = []
        list_of_ids = None
        if query_object and key in query_object:
            list_of_ids = (
                query_object[key] if isinstance(query_object[key], list) else [query_object[key]]
            )
            if len(list_of_ids) > 0:
                filters.append(entity_clazz.id.in_(list_of_ids))
            else:
                return None, None  # we don't want any entities
        else:
            filters.append(entity_clazz.allele_id.in_(allele_ids) if allele_ids else False)
            filters.append(entity_clazz.date_superceeded.is_(None))

        return filters, list_of_ids
