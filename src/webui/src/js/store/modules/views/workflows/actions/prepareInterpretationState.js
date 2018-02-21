import { deepCopy } from '../../../../../util'
import {
    setupAlleleState,
    autoReuseExistingAssessment,
    checkAddRemoveAlleleToReport
} from '../../../../common/helpers/alleleState'

/**
 * Prepares the interpretation state according to current
 * requirements. MUST be idempotent, as it will be called
 * every time the included alleles changes.
 */
export default function prepareInterpretationState({ state }) {
    const interpretation = state.get('views.workflows.interpretation.selected')
    const alleles = state.get('views.workflows.data.alleles')
    const config = state.get('app.config')

    let preparedState = deepCopy(interpretation.state)
    let preparedUserState = deepCopy(interpretation.user_state)

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

        let alleleState = preparedState.allele[aId]
        setupAlleleState(allele, alleleState)
    }

    state.set('views.workflows.interpretation.selected.state', preparedState)
    state.set('views.workflows.interpretation.selected.user_state', preparedUserState)
}
