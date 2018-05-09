import { prepareInterpretationPayload } from '../../../../common/helpers/workflow'

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
    return function finishWorkflow({ state, http, path }) {
        const type = state.get('views.workflows.type')
        const postType = TYPES[type]
        const id = state.get('views.workflows.id')
        const interpretation = state.get('views.workflows.interpretation.selected')
        const alleles = state.get('views.workflows.data.alleles')
        const references = state.get('views.workflows.data.references')

        const payload = prepareInterpretationPayload(
            type,
            id,
            interpretation,
            alleles,
            Object.values(references)
        )

        return http
            .post(`workflows/${postType}/${id}/actions/${ACTIONS[finishType]}/`, payload)
            .then((response) => {
                return path.success(response)
            })
            .catch((response) => {
                return path.error(response)
            })
    }
}
