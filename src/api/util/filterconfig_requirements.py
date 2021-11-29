from vardb.datamodel import sample
import re


def _is_family(samples):
    return len(set(s.family_id for s in samples)) == 1 and len(samples) > 1


def _is_trio(samples):
    proband_sample = next((s for s in samples if s.proband and s.mother_id and s.father_id), None)
    if not proband_sample:
        return False
    mother_sample = next((s for s in samples if s.id == proband_sample.mother_id), None)
    father_sample = next((s for s in samples if s.id == proband_sample.father_id), None)

    return bool(proband_sample and mother_sample and father_sample)


def analysis(session, analysis_id, params):
    analysis = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()

    checks = []
    if "is_trio" in params:
        checks.append(params["is_trio"] == _is_trio(analysis.samples))

    if "is_family" in params:
        checks.append(params["is_family"] == _is_family(analysis.samples))

    if "is_single" in params:
        checks.append(params["is_single"] != _is_family(analysis.samples))

    if "genepanel_name" in params:
        checks.append(re.match(params["genepanel_name"], analysis.genepanel_name) is not None)

    if "name" in params:
        checks.append(re.match(params["name"], analysis.name) is not None)

    return all(checks)
