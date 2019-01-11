from vardb.datamodel import sample


def _is_family(samples):
    return len(set(s.family_id for s in samples)) == 1


def _is_trio(samples):
    if not _is_family(samples):
        return False

    proband_sample = next(s for s in samples if s.proband)
    print(proband_sample)
    if not proband_sample.mother_id or not proband_sample.father_id:
        return False
    mother_sample = next((s for s in samples if s.id == proband_sample.mother_id), None)
    father_sample = next((s for s in samples if s.id == proband_sample.father_id), None)

    return bool(proband_sample and mother_sample and father_sample)


def analysis(session, analysis_id, params):
    analysis = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()

    checks = []
    if params.get("is_trio"):
        checks.append(params["is_trio"] == _is_trio(analysis.samples))

    if params.get("is_family"):
        checks.append(params["is_family"] == _is_family(analysis.samples))

    if params.get("is_single"):
        checks.append(params["is_single"] != _is_family(analysis.samples))

    if params.get("name"):
        checks.append(re.match(pattern, analysis.name))

    return all(checks)
