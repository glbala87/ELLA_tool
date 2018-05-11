# Avoid circular imports...
from api.v1.resources.overview import categorize_analyses_by_findings
from api import schemas


def analysis_not_ready_findings(session, analysis, interpretation):
    # Set analysis as 'Not ready' if it has warnings _or_ there are variants that needs work (verification etc)
    # TODO: Refactor this along with overview.py's functions to something nicer
    # We also need to provide configuration options for this and have postdeposit plugins
    aschema = schemas.AnalysisSchema()
    dumped_analysis = aschema.dump(analysis).data
    without_findings = bool(categorize_analyses_by_findings(
        session, [dumped_analysis])['without_findings'])

    if analysis.warnings or not without_findings:
        interpretation.workflow_status = 'Not ready'
