from vardb.datamodel import assessment, sample


def delete_analysis(session, analysis_id):
    with session.no_autoflush:
        # If any alleleassessments points to this analysis, it cannot be removed
        # We'll get an error in any case, so this check is mostly to
        # present an error to the user
        if (
            session.query(assessment.AlleleAssessment.id)
            .filter(assessment.AlleleAssessment.analysis_id == analysis_id)
            .count()
        ):
            raise RuntimeError(
                "One or more alleleassessments are pointing to this analysis. It's removal is not allowed.'"
            )

        session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).delete()
