import datetime

import hypothesis as ht
import hypothesis.strategies as st
import pytest
import pytz

from api.config import config
from datalayer.allelefilter.classificationfilter import ClassificationFilter
from vardb.datamodel import assessment

CLASSES = assessment.AlleleAssessment.classification.type.enums


@pytest.fixture(scope="function")
def assessments(session):
    assms = []
    for i, clazz in enumerate(CLASSES):
        assm = assessment.AlleleAssessment(
            user_id=1,
            allele_id=i + 1,
            classification=clazz,
            genepanel_name="HBOC",
            genepanel_version="v1.0.0",
        )
        session.add(assm)
        assms.append(assm)

    return assms


@st.composite
def filter_data(draw):
    classes = draw(
        st.lists(elements=st.sampled_from(CLASSES + ["non-existing-class"]), unique=True)
    )
    exclude_outdated = draw(st.booleans())
    allele_ids = draw(
        st.lists(
            elements=st.integers(min_value=1, max_value=len(CLASSES) * 2),
            min_size=len(CLASSES),
            unique=True,
        )
    )
    return classes, exclude_outdated, allele_ids


@st.composite
def days_since_created(draw):
    return list(draw(st.integers(min_value=0, max_value=366)) for _ in range(len(CLASSES)))


@ht.given(st.one_of(days_since_created()), st.one_of(filter_data()))
@ht.settings(deadline=500)
def test_classificationfilter(session, assessments, days_since_created, filter_data):
    classes_to_filter, exclude_outdated, allele_ids = filter_data

    has_filtered_class = set()
    has_valid_date = set()
    for assm, n_days in zip(assessments, days_since_created):
        assm.date_created = datetime.datetime.now(pytz.utc) - datetime.timedelta(n_days)

        if assm.classification in classes_to_filter:
            has_filtered_class.add(assm.allele_id)

        classification_config = next(
            (o for o in config["classification"]["options"] if o["value"] == assm.classification),
            None,
        )
        if (
            (not exclude_outdated)
            or classification_config is None
            or "outdated_after_days" not in classification_config
            or classification_config["outdated_after_days"] > n_days
        ):
            has_valid_date.add(assm.allele_id)

    expected_filtered = (has_filtered_class & has_valid_date) & set(allele_ids)

    testdata = {("dummyname", "v1.0.0"): allele_ids}

    filter_config = {"classes": classes_to_filter, "exclude_outdated": exclude_outdated}

    cf = ClassificationFilter(session, None)
    if "non-existing-class" in classes_to_filter:
        with pytest.raises(AssertionError):
            cf.filter_alleles(testdata, filter_config)
    else:
        result = cf.filter_alleles(testdata, filter_config)
        assert result[("dummyname", "v1.0.0")] == expected_filtered
