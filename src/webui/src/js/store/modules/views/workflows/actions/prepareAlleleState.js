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
    const alleles = state.get('views.workflows.interpretation.data.alleles')

    const alleleStates = state.get('views.workflows.interpretation.state.allele')
    for (let [aId, allele] of Object.entries(alleles)) {
        if (!(aId in alleleStates)) {
            alleleStates[aId] = {}
        }

        if (!('allele_id' in alleleStates[aId])) {
            alleleStates[aId]['allele_id'] = allele.id
        }

        prepareAlleleStateModel(alleleStates[aId])
        prepareAlleleAssessmentModel(alleleStates[aId].alleleassessment)
    }
    state.set('views.workflows.interpretation.state.allele', alleleStates)
}
