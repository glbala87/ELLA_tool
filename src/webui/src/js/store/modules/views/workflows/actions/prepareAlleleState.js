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

        if (!('allele_id' in alleleState[aId])) {
            alleleState[aId]['allele_id'] = aId
        }

        prepareAlleleStateModel(alleleState[aId])
        prepareAlleleAssessmentModel(alleleState[aId].alleleassessment)
    }
    state.set('views.workflows.interpretation.selected.state.allele', alleleState)
}
