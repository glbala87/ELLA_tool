import pytest
from api.allelefilter.classificationfilter import ClassificationFilter
from api.config.config import config
from vardb.datamodel import assessment

import hypothesis as ht
import hypothesis.strategies as st

@pytest.fixture(scope="function")
def classifications(session):
    c = {}
    for i in range(1,7):
        c[i] = str(i) if i < 6 else 'U'
        assm = assessment.AlleleAssessment(
            allele_id=i,
            classification=c[i],
            genepanel_name='HBOC',
            genepanel_version='v01'
        )
        session.add(assm)
    return c

@st.composite
def filter_data(draw):
    classes = draw(st.lists(elements=st.sampled_from(['1', '2', '3','4','5','U', 'DR', 'non-existing-class']), unique=True))
    allele_ids = draw(st.lists(elements=st.integers(min_value=1, max_value=10), unique=True))
    return classes, allele_ids

@ht.given(st.one_of(filter_data()))
@ht.settings(deadline=500)
def test_classificationfilter(session, classifications, filter_data):
    classes, allele_ids = filter_data

    testdata = {
        "key": allele_ids
    }

    filter_config = {
        'classes': classes
    }

    expected_result = {
        "key": set(a for a in allele_ids if classifications.get(a) in classes)
    }
    cf = ClassificationFilter(session, None)
    if "non-existing-class" in classes:
        with pytest.raises(AssertionError):
            cf.filter_alleles(testdata, filter_config)
    else:
        result = cf.filter_alleles(testdata, filter_config)
        assert result == expected_result




