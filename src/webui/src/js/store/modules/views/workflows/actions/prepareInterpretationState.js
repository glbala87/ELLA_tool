import { deepCopy } from '../../../../../util'

/**
 * Prepares the interpretation state according to current
 * requirements. MUST be idempotent, as it will be called
 * every time the included alleles changes.
 */
export default function prepareInterpretationState({ state }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')

    let preparedState = state.get('views.workflows.interpretation.state')
    let preparedUserState = state.get('views.workflows.interpretation.userState')

    if (!('allele' in preparedState)) {
        preparedState.allele = {}
    }

    if (!('manuallyAddedAlleles' in preparedState)) {
        preparedState.manuallyAddedAlleles = []
    }

    if (!('allele' in preparedUserState)) {
        preparedUserState.allele = {}
    }

    for (let [aId, allele] of Object.entries(alleles)) {
        if (!(aId in preparedState.allele)) {
            preparedState.allele[aId] = {
                allele_id: allele.id
            }
        }

        if (!(aId in preparedUserState.allele)) {
            preparedUserState.allele[aId] = {
                allele_id: allele.id,
                showExcludedReferences: false,
                sections: {}
            }
        }
    }

    state.set('views.workflows.interpretation.state', preparedState)
    state.set('views.workflows.interpretation.userState', preparedUserState)
}
