import {
    prepareAlleleStateModel,
    prepareAlleleAssessmentModel
} from '../../../../common/helpers/alleleState'

/**
 * Prepares the interpretation state according to current
 * requirements. MUST be idempotent, as it will be called
 * every time the included alleles changes.
 */
export default function prepareAlleleState({ state }) {
    const alleles = state.get('views.workflows.data.alleles')

    const alleleState = state.get('views.workflows.interpretation.selected.state.allele')
    for (let [aId, allele] of Object.entries(alleles)) {
        if (!(aId in alleleState)) {
            alleleState[aId] = {
                allele_id: allele.id
            }
        }

        prepareAlleleStateModel(alleleState[aId])
        prepareAlleleAssessmentModel(alleleState[aId].alleleassessment)

        if (allele.allele_assessment) {
            alleleState[aId].presented_alleleassessment_id = allele.allele_assessment.id
        }

        if (allele.allele_report) {
            alleleState[aId].presented_allelereport_id = allele.allele_report.id
        }
    }
    state.set('views.workflows.interpretation.selected.state.allele', alleleState)
}
