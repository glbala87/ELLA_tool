import { prepareInterpretationPayload } from '../../../../common/helpers/workflow'
import getAlleleIdsFromInterpretation from '../computed/getAlleleIdsFromInterpretation'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

const ACTIONS = {
    'Not ready': 'marknotready',
    Interpretation: 'markinterpretation',
    Review: 'markreview',
    'Medical review': 'markmedicalreview',
    Finalized: 'finalize'
}

export default function(finishType) {
    return function finishWorkflow({ state, http, path, resolve }) {
        const type = state.get('views.workflows.type')
        const postType = TYPES[type]
        const id = state.get('views.workflows.id')
        const alleles = state.get('views.workflows.interpretation.data.alleles')
        const currentState = state.get('views.workflows.interpretation.state')
        const alleleIds = resolve.value(getAlleleIdsFromInterpretation)

        const excludedAlleleIdsByCallerType = state.get(
            'views.workflows.interpretation.data.filteredAlleleIds.excluded_alleles_by_caller_type'
        )

        try {
            const payload = prepareInterpretationPayload(type, currentState, alleles, alleleIds)
            return http
                .post(`workflows/${postType}/${id}/actions/${ACTIONS[finishType]}/`, payload)
                .then((response) => {
                    return path.success(response)
                })
                .catch((response) => {
                    return path.error(response)
                })
        } catch (error) {
            console.error(error)
            return path.error({ error })
        }
    }
}
