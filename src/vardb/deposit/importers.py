#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""
import base64
import logging
import datetime
import pytz
from collections import defaultdict
from sqlalchemy import or_, and_
from os.path import commonprefix


from vardb.datamodel import allele as am, sample as sm, genotype as gm, workflow as wf, assessment
from vardb.datamodel import annotation as annm
from vardb.util import annotationconverters
from vardb.datamodel.user import User

log = logging.getLogger(__name__)


ASSESSMENT_CLASS_FIELD = "CLASS"
ASSESSMENT_COMMENT_FIELD = "ASSESSMENT_COMMENT"
ASSESSMENT_DATE_FIELD = "DATE"
ASSESSMENT_USERNAME_FIELD = "USERNAME"
REPORT_FIELD = "REPORT_COMMENT"


def commonsuffix(v):
    return commonprefix([x[::-1] for x in v])[::-1]


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in list(obj.items()))
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def has_diff_ignoring_order(ignore_order_for_key, obj1, obj2):
    csq_1 = obj1.pop(ignore_order_for_key)
    csq_2 = obj2.pop(ignore_order_for_key)
    csq1_ordered = ordered(csq_1)
    csq2_ordered = ordered(csq_2)
    csq_has_diff = not csq1_ordered == csq2_ordered
    if csq_has_diff:
        return True
    else:
        obj1[ignore_order_for_key] = csq1_ordered
        obj2[ignore_order_for_key] = csq2_ordered
        return not obj1 == obj2


def get_allele_from_record(record, alleles):
    for allele in alleles:
        if (
            allele["chromosome"] == record.variant.CHROM
            and allele["vcf_pos"] == record.variant.POS
            and allele["vcf_ref"] == record.variant.REF
            and allele["vcf_alt"] == record.variant.ALT[0]
        ):
            return allele
    return None


def build_allele_from_record(record, ref_genome):
    """Build database representation of alleles from a vcf record

    Examples (record.variant.POS - record.variant.REF - record.variant.ALT[0]):
    (showing only the non-trivial part of the returned dictionary)

    123-A-G -> {
        "start_position": 122,
        "open_end_position": 123,
        "change_type": "SNP",
        "change_from": "A",
        "change_to": "G",
    }

    123-AC-A -> {
        "start_position": 123,
        "open_end_position": 124,
        "change_type": "del",
        "change_from": "C",
        "change_to": "",
    }

    123-A-AC -> {
        "start_position": 122,
        "open_end_position": 123,
        "change_type": "ins",
        "change_from": "",
        "change_to": "C",
    }

    123-GAGA-AC -> {
        "start_position": 122,
        "open_end_position": 126,
        "change_type": "indel",
        "change_from": "GAGA",
        "change_to": "AC",
    }

    """
    assert (
        len(record.variant.ALT) == 1
    ), "Only decomposed variants are supported. That is, only one ALT per line/record."

    vcf_ref, vcf_alt, vcf_pos = record.variant.REF, record.variant.ALT[0], record.variant.POS

    ref = str(vcf_ref)
    alt = str(vcf_alt)

    # Convert to zero-based position
    pos = vcf_pos - 1

    # Remove common suffix
    # (with ref, alt = ("AGAA", "ACAA") change to ref, alt = ("AG", "AC"))
    N_suffix = len(commonsuffix([ref, alt]))
    if N_suffix > 0:
        ref, alt = ref[:-N_suffix], alt[:-N_suffix]

    # Remove common prefix and offset position
    # (with pos, ref, alt = (123, "AG", "AC") change to pos, ref, alt = (124, "G", "C"))
    N_prefix = len(commonprefix([ref, alt]))
    ref, alt = ref[N_prefix:], alt[N_prefix:]
    pos += N_prefix

    if len(ref) == len(alt) == 1:
        change_type = "SNP"
        start_position = pos
        open_end_position = pos + 1
    elif len(ref) >= 1 and len(alt) >= 1:
        assert len(ref) > 1 or len(alt) > 1
        change_type = "indel"
        start_position = pos
        open_end_position = pos + len(ref)
    elif len(ref) < len(alt):
        assert ref == ""
        change_type = "ins"
        # An insertion is shifted one base 1 because of same prefix above,
        # but the insertion is done between the reference allele (at pos-1) and the subsequent allele (at pos)
        start_position = pos - 1
        # Insertions have no span in the reference genome
        open_end_position = pos
    elif len(ref) > len(alt):
        assert alt == ""
        change_type = "del"
        start_position = pos
        open_end_position = pos + len(ref)
    else:
        raise ValueError("Unable to determine allele from ref/alt={}/{}".format(ref, alt))

    allele = {
        "genome_reference": ref_genome,
        "chromosome": record.variant.CHROM,
        "start_position": start_position,
        "open_end_position": open_end_position,
        "change_type": change_type,
        "change_from": ref,
        "change_to": alt,
        "vcf_pos": vcf_pos,
        "vcf_ref": vcf_ref,
        "vcf_alt": vcf_alt,
    }

    return allele


def is_non_empty_text(input):
    return isinstance(input, str) and input


def batch(iterable, n):
    N = len(iterable)
    for ndx in range(0, N, n):
        yield iterable[ndx : min(ndx + n, N)]


def batch_generator(generator, n):
    batch = list()
    for item in generator:
        batch.append(item)
        if len(batch) == n:
            yield batch
            batch = list()
    if batch:
        yield batch


def bulk_insert_nonexisting(
    session,
    model,
    rows,
    all_new=False,
    include_pk=None,
    compare_keys=None,
    replace=False,
    batch_size=1000,
):
    """
    Inserts data in bulk according to batch_size.

    :param model: Model to insert data into
    :type model: SQLAlchemy model
    :param rows: List of dict with data. Keys must correspond to attributes on model
    :param include_pk: Key for which to get primary key for created and existing objects.
                       Slows down performance by a lot, since we must query for the keys.
    :type include_pk: str
    :param compare_keys: Keys to be used for comparing whether an object exists already.
                         If none is provided, all keys from rows[0] will be used.
    :type compare_keys: List
    :param replace: Whether to replace (update) existing data. Requires include_pk and compare_keys.
    :param batch_size: Size of each batch that should be inserted into database. Affects memory usage.
    :yields: Type of (existing_objects, created_objects), each entry being a list of dictionaries.
             If include_pk is set, a third list is returned containing all the primary keys for the input rows.
    """

    if replace and compare_keys is None:
        raise RuntimeError(
            "Using replace=True with no supplied compare_keys makes no sense, as there can be no data to replace."
        )
    if replace and not include_pk:
        raise RuntimeError("You must supply include_pk argument when replace=True.")

    if compare_keys is None:
        compare_keys = list(rows[0].keys())

    def get_fields_filter(model, rows, compare_keys):
        q_fields = [getattr(model, k) for k in compare_keys]
        filters = []
        # Do NOT use tuple_, as tuple messes up JSONB conversion
        for row in rows:
            filters.append(and_(*[getattr(model, k) == row[k] for k in compare_keys]))
        q_filter = or_(*filters)
        return q_fields, q_filter

    for batch_rows in batch(rows, batch_size):

        q_fields, q_filter = get_fields_filter(model, batch_rows, compare_keys)
        if include_pk:
            q_fields.append(getattr(model, include_pk))
        db_existing = []
        if not all_new:
            db_existing = session.query(*q_fields).filter(q_filter).all()
            db_existing = [r._asdict() for r in db_existing]
        created = list()
        input_existing = list()

        if db_existing:
            # Filter our batch_rows based on existing in db to see which objects we need to insert
            for row in batch_rows:
                should_create = True
                for e in db_existing:
                    if all(e[k] == row[k] for k in compare_keys):
                        if include_pk:  # Copy over primary key if applicable
                            row[include_pk] = e[include_pk]
                        input_existing.append(row)
                        should_create = False
                if should_create:
                    created.append(row)
        else:
            created = batch_rows
        if replace and input_existing:
            # Reinsert all existing data
            log.debug("Replacing {} objects on {}".format(len(input_existing), str(model)))
            session.bulk_update_mappings(model, input_existing)

        session.bulk_insert_mappings(model, created)
        session.flush()
        if include_pk:
            # We need to retrieve all data back in order to match input correct with primary key
            # This is quite heavy, but much better than alternative which is sending INSERTs one
            # by one.
            q_fields = [getattr(model, k) for k in list(rows[0].keys())] + [
                getattr(model, include_pk)
            ]
            data_with_pk = session.query(*q_fields).filter(q_filter).all()
            assert len(data_with_pk) == len(created) + len(input_existing)
            for c in created:
                pk_item = next(
                    n for n in data_with_pk if all(getattr(n, k) == v for k, v in c.items())
                )
                c[include_pk] = getattr(pk_item, include_pk)
        yield input_existing, created


class SampleImporter(object):
    """
    Note: there can be multiple samples with same name in database, and they might differ in genotypes.
    This happens when multiple analyses, using the same sample data in pipeline, is imported.
    They can have been run on different regions.
    """

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)

    @staticmethod
    def parse_ped(ped_file):
        """
        Expected format is an extended .ped file with added proband ('0', '1') column

        Columns:
        family_id   sample_id   father_id   mother_id   sex affected    proband
        """

        def ped_to_sex(value):
            value = value.strip()
            if value == "1":
                return "Male"
            if value == "2":
                return "Female"
            return None

        parsed_ped = []
        with open(ped_file) as ped:
            lines = ped.readlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                family_id, sample_id, father_id, mother_id, sex, affected, proband = line.split(
                    "\t"
                )
                assert family_id, "Family ID is empty"
                assert sample_id, "Sample ID is empty"
                parsed_ped.append(
                    {
                        "family_id": family_id.strip(),
                        "sample_id": sample_id.strip(),
                        "father_id": father_id.strip(),
                        "mother_id": mother_id.strip(),
                        "sex": ped_to_sex(sex),
                        "affected": affected.strip() == "2",
                        "proband": proband.strip() == "1",
                    }
                )
        return parsed_ped

    def process(self, sample_names, analysis, sample_type="HTS", ped_file=None):

        db_samples = list()

        ped_data = None
        if ped_file:
            ped_data = self.parse_ped(ped_file)
            assert ped_data, "Provided .ped file yielded no data"
        elif len(sample_names) > 1:
            raise RuntimeError(".ped file required when importing multiple samples")

        # Connect samples to mother and/or father  {(family_id, sample_id): {'father_id': ..., 'mother_id': ...}}
        parents_to_connect = defaultdict(dict)
        for sample_idx, sample_name in enumerate(sample_names):

            sample_ped_data = {}
            if len(sample_names) == 1:
                sample_ped_data.update({"affected": True, "proband": True})

            if ped_data:
                sample_ped_data = next((p for p in ped_data if p["sample_id"] == sample_name), None)
                assert sample_ped_data, "Couldn't find sample name {} in provided .ped file".format(
                    sample_name
                )

            db_sample = sm.Sample(
                identifier=sample_name,
                sample_type=sample_type,
                analysis=analysis,
                family_id=sample_ped_data.get("family_id"),
                sex=sample_ped_data.get("sex"),
                proband=sample_ped_data.get("proband"),
                affected=sample_ped_data.get("affected"),
            )
            db_samples.append(db_sample)

            if sample_ped_data.get("mother_id") and sample_ped_data.get("mother_id") != "0":
                parents_to_connect[(sample_ped_data.get("family_id"), sample_name)][
                    "mother_id"
                ] = sample_ped_data["mother_id"]

            if sample_ped_data.get("father_id") and sample_ped_data.get("father_id") != "0":
                parents_to_connect[(sample_ped_data.get("family_id"), sample_name)][
                    "father_id"
                ] = sample_ped_data["father_id"]

            self.session.add(db_sample)
            self.counter["nSamplesAdded"] += 1

        # We need to flush to create ids before we connect them
        self.session.flush()

        if not db_samples or len(db_samples) != len(sample_names):
            self.session.rollback()
            raise RuntimeError(
                "Couldn't import samples to database. (db_samples: {}, sample_names: {})".format(
                    db_samples, sample_names
                )
            )

        # Siblings
        # There are two possible cases:
        # - Proband has parents, if so all samples sharing parents will be siblings
        # - Proband doesn't have parents (ids are '0'), if so all other samples are considered siblings

        proband_sample = next(s for s in db_samples if s.proband)
        # Proband has no parents
        if not parents_to_connect:
            sibling_samples = [s for s in db_samples if s.proband is False]
            assert len(sibling_samples) + 1 == len(db_samples)
            for sibling_sample in sibling_samples:
                sibling_sample.sibling_id = proband_sample.id
        else:
            # Proband has parents
            # Connect all parents
            for fam_sample_id, values in parents_to_connect.items():
                family_id, sample_id = fam_sample_id
                db_sample = next(s for s in db_samples if s.identifier == sample_id)
                if values.get("father_id"):
                    db_father = next(s for s in db_samples if s.identifier == values["father_id"])
                    db_sample.father_id = db_father.id
                if values.get("mother_id"):
                    db_mother = next(s for s in db_samples if s.identifier == values["mother_id"])
                    db_sample.mother_id = db_mother.id
            # Connect siblings to proband
            sibling_samples = [
                s
                for s in db_samples
                if s.father_id == proband_sample.father_id
                and s.mother_id == proband_sample.mother_id
                and s.proband is False
            ]
            for sibling_sample in sibling_samples:
                sibling_sample.sibling_id = proband_sample.id

        family_ids = [s.family_id for s in db_samples]

        if ped_file is None:
            assert (
                family_ids == [None] and len(db_samples) == 1
            ), "Cannot import multiple samples without pedigree file"

        proband_count = len([True for s in db_samples if s.proband])
        assert proband_count == 1, "Exactly one sample as proband is required. Got {}.".format(
            proband_count
        )
        father_count = len(set([s.father_id for s in db_samples if s.father_id is not None]))
        assert father_count < 2, "An analysis' family can only have one father."
        mother_count = len(set([s.mother_id for s in db_samples if s.mother_id is not None]))
        assert mother_count < 2, "An analysis' family can only have one mother."

        assert len(set(family_ids)) == 1, "Only one family id is supported. Got {}.".format(
            ",".join(family_ids)
        )
        return db_samples


class GenotypeImporter(object):
    def __init__(self, session):
        self.session = session
        self.batch_items = list()  # [{'genotype': .., 'genotypesampledata: [...]}]

        self.types = {
            (0, 1): "Heterozygous",  # "0/1"
            (1, 0): "Heterozygous",  # "1/0"
            (1, -1): "Heterozygous",  # "1/."
            (-1, 1): "Heterozygous",  # "./1"
            (1, 1): "Homozygous",  # "1/1"
            (1,): "Homozygous",  # "1"
            (0, -1): "Reference",  # Not applicable to proband samples # "0/."
            (-1, 0): "Reference",  # Not applicable to proband samples # "./0"
            (0, 0): "Reference",  # Not applicable to proband samples # "0/0"
            (-1, -1): "Reference",  # Note exception in add(), # "./."
            (-1,): "Reference",  # Note exception in add(), # "."
            (0,): "Reference",  # "0"
        }

    def add(
        self,
        records,
        alleles,
        proband_sample_name,
        samples,
        samples_missing_coverage,
        block_records,
    ):
        """
        Add genotypes for provided record. We only create genotypes for the proband_sample_name,
        while we add genotypesampledata records for all samples (connected to the proband sample's genotype).
        See datamodel for more information.
        """

        proband_sample_id = next(s.id for s in samples if s.identifier == proband_sample_name)

        a1 = alleles[0]
        a2 = None

        # For biallelic -> set correct first and second allele
        if len(alleles) == 2:
            for record in records:
                record_proband_gt = record.sample_genotype(proband_sample_name)
                assert record_proband_gt in [(1, -1), (-1, 1)]
                allele = get_allele_from_record(record, alleles)
                if record_proband_gt == (1, -1):
                    a1 = allele
                elif record_proband_gt == (-1, 1):
                    a2 = allele

            assert a1 and a2

        assert a1 != a2

        # FILTER and QUAL should be same for all decomposed records
        filter_status = records[0].get_raw_filter()
        try:
            qual = int(records[0].variant.QUAL)
        except (ValueError, TypeError):
            qual = None

        # Create genotype item
        genotype_item = {
            "allele_id": a1["id"],
            "secondallele_id": a2["id"] if a2 is not None else None,
            "sample_id": proband_sample_id,
            "filter_status": filter_status,
            "variant_quality": qual,
        }

        # Calculate AD
        # This is unexpectedly complex due the decomposition and the fact
        # that we want to keep AD for variants that are not the proband's.
        # We go through all the records for the block for each sample
        sample_allele_depth = defaultdict(dict)  # {sample_name: {'REF': 12, 'A': 134, 'G': 12}}
        for sample in samples:
            for block_record in block_records:
                s_ad = block_record.get_format_sample("AD", sample.identifier)

                # Sanity check
                if any(x is None for x in s_ad):
                    assert all(x is None for x in s_ad)

                if not all(x is None for x in s_ad):
                    if len(s_ad) == 2:
                        sample_allele_depth[sample.identifier].update(
                            {
                                "REF ({})".format(block_record.variant.REF): int(s_ad[0]),
                                block_record.variant.ALT[0]: int(s_ad[1]),
                            }
                        )
                    else:
                        log.warning(
                            f"AD not decomposed ({s_ad})! Allele depth value will be empty."
                        )

        # When normalizing a multiallelic site, we might get multiple refs. This is a double count and affects the allele ratio.
        # Therefore, there should only be one REF-key in the dict.
        for sample in sample_allele_depth:
            refs = list(k for k in sample_allele_depth[sample] if k.startswith("REF"))
            if len(refs) > 1:
                ref_count = sample_allele_depth[sample][refs[0]]
                # Remove all ref counts
                assert all([sample_allele_depth[sample].pop(ref) == ref_count for ref in refs])
                # Insert ref count under REF-key
                sample_allele_depth[sample]["REF"] = ref_count

        # Create genotypesampledata items
        genotypesampledata_items = list()
        for sample in samples:
            for record in records:
                assert len(record.variant.ALT) == 1
                secondallele = False

                # If a secondallele exists, check if this record is the secondallele
                if a2:
                    allele = get_allele_from_record(record, alleles)
                    secondallele = allele == a2

                sample_genotype = record.sample_genotype(sample.identifier)
                assert (
                    sample_genotype in self.types
                ), "Not supported genotype {} for sample {}".format(
                    sample_genotype, sample.identifier
                )

                # If REF or POS is shifted, we can't trust the AD data.
                allele_ratio = 0
                if (
                    len(set([r.variant.POS for r in records])) != 1
                    or len(set([r.variant.REF for r in records])) != 1
                ):
                    allele_depth = {}
                else:
                    allele_depth = sample_allele_depth[sample.identifier]
                    allele_sum = sum(allele_depth.values())
                    if allele_sum:
                        allele_ratio = float(allele_depth[record.variant.ALT[0]]) / allele_sum

                multiallelic = sample_genotype in [
                    (1, -1),
                    (-1, 1),
                    (0, -1),
                    (-1, 0),
                ]  # sample is multiallelic for this site

                # PL is misleading for all samples on multiallelic sites due to decomposition
                if multiallelic:
                    genotype_likelihood = None
                else:
                    genotype_likelihood = record.get_format_sample("PL", sample.identifier)

                if (
                    sample_genotype in [(-1, -1), (-1,)]
                    and sample.identifier in samples_missing_coverage
                ):
                    genotype_type = "No coverage"
                else:
                    genotype_type = self.types[sample_genotype]

                genotypesampledata_item = {
                    "type": genotype_type,
                    "secondallele": secondallele,
                    "sample_id": sample.id,
                    "genotype_quality": record.get_format_sample(
                        "GQ", sample.identifier, scalar=True
                    ),
                    "genotype_likelihood": genotype_likelihood,
                    "sequencing_depth": record.get_format_sample(
                        "DP", sample.identifier, scalar=True
                    ),
                    "allele_depth": allele_depth,
                    "allele_ratio": allele_ratio,
                    "multiallelic": multiallelic,
                }

                genotypesampledata_items.append(genotypesampledata_item)

        self.batch_items.append(
            {"genotype": genotype_item, "genotypesampledata_items": genotypesampledata_items}
        )

    def process(self):

        if not self.batch_items:
            return list(), list()

        result_genotypes = list()
        result_genotypesampledata = list()

        genotypes = [item["genotype"] for item in self.batch_items]
        for existing, created in bulk_insert_nonexisting(
            self.session,
            gm.Genotype,
            genotypes,
            all_new=True,
            include_pk="id",
            replace=False,
            batch_size=len(genotypes),
        ):
            # Insert the created genotype_id into the corresponding genotypesampledata
            for c in created:
                for item in self.batch_items:
                    if (
                        item["genotype"]["allele_id"] == c["allele_id"]
                        and item["genotype"]["secondallele_id"] == c["secondallele_id"]
                    ):
                        for gsd in item["genotypesampledata_items"]:
                            gsd["genotype_id"] = c["id"]
            assert len(existing) == 0
            result_genotypes.extend(created)

        genotypesampledata = list()
        for item in self.batch_items:
            genotypesampledata.extend(item["genotypesampledata_items"])
        for existing, created in bulk_insert_nonexisting(
            self.session,
            gm.GenotypeSampleData,
            genotypesampledata,
            all_new=True,
            replace=False,
            batch_size=len(genotypesampledata),
        ):
            assert len(existing) == 0
            result_genotypesampledata.extend(created)

        self.batch_items = list()
        return result_genotypes, result_genotypesampledata


class AssessmentImporter(object):
    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)
        self.batch_items = list()

    def add(self, record, allele_id, gp_name, gp_version):
        assert (
            len(record.variant.ALT) == 1
        ), "Only decomposed variants are supported. That is, only one ALT per line/record."

        all_info = record.annotation()

        class_raw = all_info.get(ASSESSMENT_CLASS_FIELD)
        if not is_non_empty_text(class_raw) or class_raw not in (
            "1",
            "2",
            "3",
            "4",
            "5",
            "DR",
            "RF",
            "NP",
        ):
            logging.warning("Unknown class {}".format(class_raw))
            return

        # Get required fields
        ass_info = {
            "allele_id": allele_id,
            "classification": class_raw,
            "evaluation": {"classification": {"comment": "Comment missing."}},
        }

        assessment_comment = all_info.get(ASSESSMENT_COMMENT_FIELD)
        if is_non_empty_text(assessment_comment):
            ass_info["evaluation"]["classification"].update(
                {"comment": base64.b64decode(assessment_comment).decode("utf-8")}
            )

        username_raw = all_info.get(ASSESSMENT_USERNAME_FIELD)
        ass_info["username"] = username_raw

        date_created = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)  # Set to epoch if not proper
        date_raw = all_info.get(ASSESSMENT_DATE_FIELD)
        if is_non_empty_text(date_raw):
            try:
                date_created = datetime.datetime.strptime(date_raw, "%Y-%m-%d")
            except ValueError:
                pass
        ass_info["date_created"] = date_created
        ass_info["genepanel_name"] = gp_name
        ass_info["genepanel_version"] = gp_version

        self.batch_items.append(ass_info)
        return ass_info

    def process(self):
        """
        Add assessment of allele if present.
        """

        if not self.batch_items:
            return list()

        results = list()

        for item in self.batch_items:
            username = item.pop("username")
            item["user_id"] = self.session.query(User.id).filter(User.username == username).scalar()

        for existing, created in bulk_insert_nonexisting(
            self.session,
            assessment.AlleleAssessment,
            self.batch_items,
            compare_keys=["allele_id"],
            replace=False,
            batch_size=len(self.batch_items),  # Insert whole batch
        ):
            results.extend(created)
            self.counter["nAssessmentsSkipped"] += len(existing)
            self.counter["nNovelAssessments"] += len(created)
        self.batch_items = list()

        return results


class AnnotationImporter(object):
    def __init__(self, session):
        self.session = session
        self.batch_items = list()
        self.csq_converter = annotationconverters.ConvertCSQ()

    def _extract_annotation_from_record(self, record, allele):
        """Given a record, return dict with annotation to be stored in db."""
        # Deep merge 'ALL' annotation and allele specific annotation
        merged_annotation = record.annotation()

        # # Convert the mess of input annotation into database annotation format
        frequencies = dict()
        frequencies.update(annotationconverters.gnomad_genomes_frequencies(merged_annotation))
        frequencies.update(annotationconverters.gnomad_exomes_frequencies(merged_annotation))
        frequencies.update(annotationconverters.indb_frequencies(merged_annotation))

        transcripts = self.csq_converter(
            merged_annotation.get("CSQ"),
            next((x for x in record.meta.get("INFO", []) if x.get("ID") == "CSQ"), None),
        )

        external = dict()
        external.update(annotationconverters.convert_hgmd(merged_annotation))
        external.update(annotationconverters.convert_clinvar(merged_annotation))

        references = annotationconverters.ConvertReferences().process(
            merged_annotation, record.meta
        )

        annotations = {
            "frequencies": frequencies,
            "external": external,
            "prediction": {},
            "transcripts": sorted(transcripts, key=lambda x: x["transcript"]),
            "references": references,
        }
        return annotations

    def add(self, record, allele_id):

        allele = record.variant.ALT[0]

        annotation_data = self._extract_annotation_from_record(record, allele)
        data = {"allele_id": allele_id, "annotations": annotation_data, "date_superceeded": None}
        self.batch_items.append(data)
        return data

    def process(self):
        if not self.batch_items:
            return list()

        results = list()

        # If annotation exists already for allele_id:
        # - If annotation data is different we create new item with link to old
        #   and supercede the old one
        # - If annotation data is the same, we do nothing

        filters = list()
        # Do not use tuple_ since JSONB comparison doesn't work
        for item in self.batch_items:
            filters.append(
                and_(
                    *[
                        annm.Annotation.allele_id == item["allele_id"],
                        annm.Annotation.annotations != item["annotations"],
                        annm.Annotation.date_superceeded.is_(None),
                    ]
                )
            )
        exists_with_different = (
            self.session.query(annm.Annotation.id, annm.Annotation.allele_id)
            .filter(or_(*filters))
            .all()
        )

        to_supercede = list()
        for e in exists_with_different:
            now = datetime.datetime.now(pytz.utc)
            to_supercede.append({"date_superceeded": now, "id": e.id})

        if to_supercede:
            self.session.bulk_update_mappings(annm.Annotation, to_supercede)

        for existing, created in bulk_insert_nonexisting(
            self.session,
            annm.Annotation,
            self.batch_items,
            include_pk="id",
            compare_keys=["allele_id", "annotations", "date_superceeded"],
            replace=False,
            batch_size=len(self.batch_items),  # Insert whole batch
        ):
            to_supercede = list()
            to_link_previous = list()
            for c in created:
                # Link new created ones to the ones superceded earlier
                existing_annotation_id = next(
                    (e.id for e in exists_with_different if e.allele_id == c["allele_id"]), None
                )
                if existing_annotation_id:
                    to_link_previous.append(
                        {"id": c["id"], "previous_annotation_id": existing_annotation_id}
                    )

            if to_link_previous:
                self.session.bulk_update_mappings(annm.Annotation, to_link_previous)

            results.extend(existing + created)
        self.batch_items = list()
        return results


class AlleleImporter(object):
    def __init__(self, session, ref_genome="GRCh37"):
        self.session = session
        self.ref_genome = ref_genome
        self.counter = defaultdict(int)
        self.batch_items = list()  # Items for batch processing

    def add(self, record):
        """
        Adds a new record to internal batch
        """

        item = build_allele_from_record(record, self.ref_genome)
        self.batch_items.append(item)

        self.counter["nAltAlleles"] += 1
        return item

    def process(self):
        if not self.batch_items:
            return list()
        results = list()
        for existing, created in bulk_insert_nonexisting(
            self.session,
            am.Allele,
            self.batch_items,
            include_pk="id",
            replace=False,
            batch_size=len(self.batch_items),  # Insert whole batch
        ):
            results.extend(existing + created)
        self.batch_items = list()
        return results


class AnalysisImporter(object):
    def __init__(self, session):
        self.session = session

    def process(self, analysis_name, genepanel, report, warnings, date_requested=None):
        """Create analysis with a default gene panel for a sample"""

        if (
            self.session.query(sm.Analysis)
            .filter(sm.Analysis.name == analysis_name, genepanel == genepanel)
            .count()
        ):
            raise RuntimeError("Analysis {} is already imported.".format(analysis_name))

        if isinstance(date_requested, str):
            date_requested = datetime.datetime.strptime(date_requested, "%Y-%m-%d")

        analysis = sm.Analysis(
            name=analysis_name,
            genepanel=genepanel,
            date_requested=date_requested,
            report=report,
            warnings=warnings,
        )

        self.session.add(analysis)
        return analysis

    def get(self, analysis_name, genepanel):
        return (
            self.session.query(sm.Analysis)
            .filter(sm.Analysis.name == analysis_name, genepanel == genepanel)
            .one()
        )


class AnalysisInterpretationImporter(object):
    def __init__(self, session):
        self.session = session

    def process(self, db_analysis, priority, reopen_if_exists=False):
        # Get latest interpretation (largest ID), if exists
        existing = (
            self.session.query(wf.AnalysisInterpretation)
            .filter(wf.AnalysisInterpretation.analysis_id == db_analysis.id)
            .order_by(wf.AnalysisInterpretation.id.desc())
            .limit(1)
            .one_or_none()
        )

        if not existing:
            db_interpretation, _ = wf.AnalysisInterpretation.get_or_create(
                self.session,
                analysis=db_analysis,
                genepanel=db_analysis.genepanel,
                status="Not started",
            )
            self.session.flush()

            # If special priority is given, insert log entry
            if priority:
                interpretation_log = wf.InterpretationLog(
                    analysisinterpretation_id=db_interpretation.id, priority=priority
                )
                self.session.add(interpretation_log)
        else:
            # If the existing is Done, we reopen the analysis since we have added new
            if reopen_if_exists and existing.status == "Done":
                import api.v1.resources.workflow.helpers as helpers  # TODO: Placed here due to circular imports...

                db_interpretation = helpers.reopen_interpretation(
                    self.session, workflow_analysis_id=existing.analysis_id
                )[1]
            else:
                db_interpretation = None
        return db_interpretation


class AlleleInterpretationImporter(object):
    def __init__(self, session):
        self.session = session

    def process(self, genepanel, allele_id):
        existing = (
            self.session.query(wf.AlleleInterpretation)
            .filter(wf.AlleleInterpretation.allele_id == allele_id)
            .limit(1)
            .one_or_none()
        )

        if not existing:
            db_interpretation, _ = wf.AlleleInterpretation.get_or_create(
                self.session, allele_id=allele_id, genepanel=genepanel, status="Not started"
            )
        else:
            # Do not create a new interpretation entry if existing
            db_interpretation = None
        return db_interpretation
