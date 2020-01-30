import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from './getAlleleState'
import isAlleleAssessmentReused from './isAlleleAssessmentReused'

export default (allele) => {
    return Compute(allele, state`views.workflows.data.analysis.id`, (allele, analysisId, get) => {
        if (!allele || !analysisId) {
            return null
        }

        const alleleState = get(getAlleleState(allele.id))
        const reused = get(isAlleleAssessmentReused(allele.id))
        if (
            allele.allele_assessment &&
            allele.allele_assessment.analysis_id === analysisId &&
            reused
        ) {
            return 'finalized'
        } else if (alleleState && alleleState.workflow && alleleState.workflow.reviewed) {
            return 'reviewed'
        } else {
            return null
        }
    })
}
