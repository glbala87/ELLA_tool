from vardb.util import DB
from vardb.datamodel import annotation
import pytest


def test_mutable_json(session):
    """
    Not the place to test this, but need to test it on a live postgres db...
    Test that the custom mutation tracking is working.
    """

    # Test mutating a customannotation objects data
    ca = annotation.CustomAnnotation()
    ca.annotations = {
        'test': list()
    }

    session.add(ca)
    session.commit()

    db_ca = session.query(annotation.CustomAnnotation).filter(annotation.CustomAnnotation.id == ca.id).one()

    db_ca.annotations['test'].append({'nested_test': {}})
    assert len(session.dirty)
    session.commit()

    db_ca = session.query(annotation.CustomAnnotation).filter(annotation.CustomAnnotation.id == ca.id).one()
    assert db_ca.annotations['test'][0] == {'nested_test': {}}
    db_ca.annotations['test'][0]['nested_test']['nested_nested_field'] = 4
    assert len(session.dirty)
    session.commit()

    db_ca = session.query(annotation.CustomAnnotation).filter(annotation.CustomAnnotation.id == ca.id).one()
    assert db_ca.annotations['test'][0]['nested_test']['nested_nested_field'] == 4

    # Cleanup
    session.delete(ca)
    session.commit()
