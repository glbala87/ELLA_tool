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

    // Loop first over alleles in backend to create non-existing objects
    for (const aId of Object.keys(alleles)) {
        if (!(aId in alleleStates)) {
            alleleStates[aId] = {}
        }
    }

    // Allele ids might not be part of alleles returned from backend (e.g. filtered),
    // but we want to migrate all state to match state schema
    for (const aId of Object.keys(alleleStates)) {
        if (!('allele_id' in alleleStates[aId])) {
            alleleStates[aId]['allele_id'] = parseInt(aId)
        }

        prepareAlleleStateModel(alleleStates[aId])
        prepareAlleleAssessmentModel(alleleStates[aId].alleleassessment, parseInt(aId))
    }
    state.set('views.workflows.interpretation.state.allele', alleleStates)
}
