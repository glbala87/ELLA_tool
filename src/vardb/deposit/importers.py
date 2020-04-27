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
import itertools
from collections import defaultdict
from sqlalchemy import tuple_, or_, and_
from sqlalchemy.orm.exc import NoResultFound


from vardb.datamodel import allele as am, sample as sm, genotype as gm, workflow as wf, assessment
from vardb.datamodel import annotation as annm, assessment as asm
from vardb.util import vcfiterator, annotationconverters
from vardb.deposit.vcfutil import vcfhelper
from vardb.datamodel.user import User

log = logging.getLogger(__name__)


ASSESSMENT_CLASS_FIELD = "CLASS"
ASSESSMENT_COMMENT_FIELD = "ASSESSMENT_COMMENT"
ASSESSMENT_DATE_FIELD = "DATE"
ASSESSMENT_USERNAME_FIELD = "USERNAME"
REPORT_FIELD = "REPORT_COMMENT"


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
            allele["chromosome"] == record["CHROM"]
            and allele["vcf_pos"] == record["POS"]
            and allele["vcf_ref"] == record["REF"]
            and allele["vcf_alt"] == record["ALT"][0]
        ):
            return allele
    return None


def deepmerge(source, destination):
    """
    Deepmerge dicts.
    http://stackoverflow.com/a/20666342

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in list(source.items()):
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            deepmerge(value, node)
        else:
            destination[key] = value

    return destination


def is_non_empty_text(input):
    return isinstance(input, str) and input


def batch(iterable, n):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]


def batch_generator(generator, n):
    batch = list()
    for item in generator():
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
            "0/1": "Heterozygous",
            "1/.": "Heterozygous",
            "./1": "Heterozygous",
            "1/1": "Homozygous",
            "0/.": "Reference",  # Not applicable to proband samples
            "0/0": "Reference",  # Not applicable to proband samples
            "./.": "Reference",  # Note exception in add()
        }

    def is_sample_hom(self, record):
        gt1, gt2 = record["GT"].split("/", 1)
        return gt1 == gt2 == "1"

    def remove_phasing(self, record):
        phasing_removed = False
        for sample in record["SAMPLES"]:
            if "|" in record["SAMPLES"][sample]["GT"]:
                phasing_removed = True
                record["SAMPLES"][sample]["GT"] = (
                    record["SAMPLES"][sample]["GT"]
                    .replace("|", "/")
                    .replace("1/0", "0/1")
                    .replace("./0", "0/.")
                )
        return phasing_removed

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

        :note: Phasing will be ignored.
        """

        phasing_removed = any([self.remove_phasing(record) for record in records])
        if phasing_removed:
            log.warning("Phased data detected. Phasing will be ignored.")

        proband_sample_id = next(s.id for s in samples if s.identifier == proband_sample_name)

        a1 = alleles[0]
        a2 = None

        # For biallelic -> set correct first and second allele
        if len(alleles) == 2:
            for record in records:
                record_sample = record["SAMPLES"][proband_sample_name]
                assert record_sample["GT"] in ["1/.", "./1"]
                allele = get_allele_from_record(record, alleles)
                if record_sample["GT"] == "1/.":
                    a1 = allele
                elif record_sample["GT"] == "./1":
                    a2 = allele

            assert a1 and a2

        assert a1 != a2

        # FILTER and QUAL should be same for all decomposed records
        filter_status = records[0]["FILTER"]
        try:
            qual = int(records[0]["QUAL"])
        except ValueError:
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
                block_record_sample = block_record["SAMPLES"][sample.identifier]
                if block_record_sample.get("AD"):
                    if len(block_record_sample["AD"]) == 2:
                        sample_allele_depth[sample.identifier].update(
                            {
                                "REF ({})".format(block_record["REF"]): block_record_sample["AD"][
                                    0
                                ],
                                block_record["ALT"][0]: block_record_sample["AD"][1],
                            }
                        )
                    else:
                        log.warning("AD not decomposed! Allele depth value will be empty.")

        # Create genotypesampledata items
        genotypesampledata_items = list()
        for sample in samples:
            for record in records:
                assert len(record["ALT"]) == 1
                secondallele = False

                # If a secondallele exists, check if this record is the secondallele
                if a2:
                    allele = get_allele_from_record(record, alleles)
                    secondallele = allele == a2

                record_sample = record["SAMPLES"][sample.identifier]
                assert (
                    record_sample["GT"] in self.types
                ), "Not supported genotype {} for sample {}".format(
                    record_sample["GT"], sample_name
                )

                # If REF or POS is shifted, we can't trust the AD data.
                allele_ratio = 0
                if (
                    len(set([r["POS"] for r in records])) != 1
                    or len(set([r["REF"] for r in records])) != 1
                ):
                    allele_depth = {}
                else:
                    allele_depth = sample_allele_depth[sample.identifier]
                    allele_sum = sum(allele_depth.values())
                    if allele_sum:
                        allele_ratio = float(allele_depth[record["ALT"][0]]) / sum(
                            allele_depth.values()
                        )

                genotype_quality = record_sample.get("GQ")
                if not isinstance(genotype_quality, int):
                    genotype_quality = None

                sequencing_depth = record_sample.get("DP")
                if not isinstance(sequencing_depth, int):
                    sequencing_depth = None

                multiallelic = record_sample["GT"] in [
                    "1/.",
                    "./1",
                    "0/.",
                    "./0",
                ]  # sample is multiallelic for this site

                genotype_likelihood = record_sample.get("PL")
                # PL is misleading for all samples on multiallelic sites due to decomposition
                if not isinstance(genotype_likelihood, list) or multiallelic:
                    genotype_likelihood = None

                if record_sample["GT"] == "./." and sample.identifier in samples_missing_coverage:
                    genotype_type = "No coverage"
                else:
                    genotype_type = self.types[record_sample["GT"]]

                genotypesampledata_item = {
                    "type": genotype_type,
                    "secondallele": secondallele,
                    "sample_id": sample.id,
                    "genotype_quality": genotype_quality,
                    "genotype_likelihood": genotype_likelihood,
                    "sequencing_depth": sequencing_depth,
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
            len(record["ALT"]) == 1
        ), "Only decomposed variants are supported. That is, only one ALT per line/record."
        allele = record["ALT"][0]

        all_info = record["INFO"]["ALL"]

        class_raw = all_info.get(ASSESSMENT_CLASS_FIELD)
        if not is_non_empty_text(class_raw) or class_raw not in ("1", "2", "3", "4", "5", "U"):
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

        user = None
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


class SplitToDictInfoProcessor(vcfiterator.BaseInfoProcessor):
    """
    For use with VcfIterator
    Splits keys like HGMD__HGMDMUT_key{n} to a dictionary:
    {
        'HGMD': {
            'HGMDMUT': {
                'key1': value
                'key2': value
            }
        }
    }
    """

    def __init__(self, meta):
        self.meta = meta

    def accepts(self, key, value, processed):
        if processed:
            return False
        return "__" in key

    def process(self, key, value, info_data, alleles, processed):
        keys = key.split("__")
        func = self.getConvertFunction(self.meta, key)

        node = info_data["ALL"]
        # Create or search nested structure
        while keys:
            k = keys.pop(0)
            new_node = node.get(k)
            if new_node is None:
                node[k] = dict()
                if keys:
                    node = node[k]
            else:
                node = new_node
        # Insert value on inner node (dict)
        if isinstance(value, str):
            value = vcfhelper.translate_to_original(value)
            node[k] = func(value)
        else:
            node[k] = value


class HGMDInfoProcessor(SplitToDictInfoProcessor):
    """
    Processes HGMD data, specifically parsing the extrarefs data into a list.

    Builds on top of SplitToDictInfoProcessor, since it's a special case of same functionality.
    """

    def __init__(self, meta):
        self.meta = meta
        self.fields = self._parseFormat()

    def _parseFormat(self):

        field = next((e for e in self.meta["INFO"] if e["ID"] == "HGMD__extrarefs"), None)
        if not field:
            return None
        fields = field["Description"].split("(")[1].split(")")[0].split("|")
        return fields

    def accepts(self, key, value, processed):
        if key.startswith("HGMD__"):
            return True

    def _parseExtraRef(self, value):
        entries = [
            dict(list(zip(self.fields, [vcfhelper.translate_to_original(e) for e in v.split("|")])))
            for v in value.split(",")
        ]
        for e in entries:
            for t in ["pmid"]:
                if e.get(t):
                    try:
                        e[t] = int(e[t])
                    # If value is not int, it's not valid pmid. Remove key from data.
                    except ValueError:
                        del e[t]
            for k, v in dict(e).items():
                if v == "":
                    del e[k]
        return entries

    def process(self, key, value, info_data, alleles, processed):
        section, hgmd_key = key.split("__", 1)
        # Process data using SplitToDictInfoProcessor
        super(HGMDInfoProcessor, self).process(key, value, info_data, alleles, processed)

        # Now our data should be in info_dict['ALL']['HGMD']
        # If the key is extrarefs, we overwrite it with the parsed version
        if self.fields:
            if hgmd_key == "extrarefs":
                info_data["ALL"][section]["extrarefs"] = self._parseExtraRef(value)
        elif hgmd_key == "pmid":
            info_data["ALL"][section]["pmid"] = int(info_data["ALL"][section]["pmid"])


class AnnotationImporter(object):
    def __init__(self, session):
        self.session = session
        self.batch_items = list()
        self.csq_converter = annotationconverters.ConvertCSQ()

    def _extract_annotation_from_record(self, record, allele):
        """Given a record, return dict with annotation to be stored in db."""
        # Deep merge 'ALL' annotation and allele specific annotation
        merged_annotation = deepmerge(record["INFO"]["ALL"], record["INFO"][allele])

        # Convert the mess of input annotation into database annotation format
        frequencies = dict()
        frequencies.update(annotationconverters.exac_frequencies(merged_annotation))
        frequencies.update(annotationconverters.gnomad_genomes_frequencies(merged_annotation))
        frequencies.update(annotationconverters.gnomad_exomes_frequencies(merged_annotation))
        frequencies.update(annotationconverters.csq_frequencies(merged_annotation))
        frequencies.update(annotationconverters.indb_frequencies(merged_annotation))

        transcripts = self.csq_converter(merged_annotation)

        external = dict()
        external.update(annotationconverters.convert_hgmd(merged_annotation))
        external.update(annotationconverters.convert_clinvar(merged_annotation))

        references = annotationconverters.ConvertReferences().process(merged_annotation)

        annotations = {
            "frequencies": frequencies,
            "external": external,
            "prediction": {},
            "transcripts": sorted(transcripts, key=lambda x: x["transcript"]),
            "references": references,
        }
        return annotations

    def add(self, record, allele_id):

        assert (
            len(record["ALT"]) == 1
        ), "Only decomposed variants are supported. That is, only one ALT per line/record."
        allele = record["ALT"][0]

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

        assert (
            len(record["ALT"]) == 1
        ), "Only decomposed variants are supported. That is, only one ALT per line/record."

        alt = record["ALT"][0]
        start_offset, allele_length, change_type, change_from, change_to = vcfhelper.compare_alleles(
            record["REF"], alt
        )
        start_pos = vcfhelper.get_start_position(record["POS"], start_offset, change_type)
        end_pos = vcfhelper.get_end_position(record["POS"], start_offset, allele_length)

        vcf_pos = record["POS"]
        vcf_ref = record["REF"]
        vcf_alt = alt

        item = {
            "genome_reference": self.ref_genome,
            "chromosome": record["CHROM"],
            "start_position": start_pos,
            "open_end_position": end_pos,
            "change_from": change_from,
            "change_to": change_to,
            "change_type": change_type,
            "vcf_pos": vcf_pos,
            "vcf_ref": vcf_ref,
            "vcf_alt": vcf_alt,
        }
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
                    self.session, analysis_id=existing.analysis_id
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
