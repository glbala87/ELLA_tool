from vardb.datamodel import assessment, workflow, sample, genotype


def delete_analysis(session, analysis_id):
    with session.no_autoflush:
        # If any alleleassessments points to this analysis, it cannot be removed
        # We'll get an error in any case, so this check is mostly to
        # present an error to the user
        if session.query(assessment.AlleleAssessment.id).filter(
            assessment.AlleleAssessment.analysis_id == analysis_id
        ).count():
            raise RuntimeError(
                "One or more alleleassessments are pointing to this analysis. It's removal is not allowed.'")

        analysis = session.query(sample.Analysis).join(
            sample.Sample,
            genotype.Genotype
        ).filter(
            sample.Analysis.id == analysis_id
        ).one()

        # Remove samples and genotypes
        samples = analysis.samples
        for s in samples:
            for g in s.genotypes:
                for gsd in g.genotypesampledata:
                    session.delete(gsd)
                session.delete(g)
            session.delete(s)

        # Clean up corresponding interpretationsnapshot entries
        snapshots = session.query(workflow.AnalysisInterpretationSnapshot).filter(
            workflow.AnalysisInterpretation.analysis_id == analysis_id,
            workflow.AnalysisInterpretationSnapshot.analysisinterpretation_id == workflow.AnalysisInterpretation.id
        ).all()
        for snapshot in snapshots:
            session.delete(snapshot)

        interpretations = session.query(workflow.AnalysisInterpretation).filter(
            workflow.AnalysisInterpretation.analysis_id == analysis_id,
        ).all()
        for i in interpretations:
            logentries = session.query(workflow.InterpretationLog).filter(
                workflow.InterpretationLog.analysisinterpretation_id == i.id
            ).all()
            for le in logentries:
                session.delete(le)
            statehistories = session.query(workflow.InterpretationStateHistory).filter(
                workflow.InterpretationStateHistory.analysisinterpretation_id == i.id
            ).all()
            for sh in statehistories:
                session.delete(sh)

            session.delete(i)

        # Finally, delete analysis
        session.delete(analysis)
