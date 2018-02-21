import { prepareInterpretationPayload } from '../../../../common/helpers/workflow'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function(finishType) {
    return function finishWorkflow({ state, http, path }) {
        const type = TYPES[state.get('views.workflows.type')]
        const id = state.get('views.workflows.id')
        const interpretation = state.get('views.workflows.interpretation.selected')
        const alleles = state.get('views.workflows.data.alleles')

        if (!['markreview', 'finalize'].find(e => e === finishType)) {
            console.error(`'Invalid finishType ${finishType}`)
            return path.error()
        }

        if (interpretation.status !== 'Ongoing') {
            console.error('Trying to mark review when interpretation status is not Ongoing')
            return path.error()
        }

        const payload = prepareInterpretationPayload(type, id, interpretation, alleles)

        return http
            .post(`workflows/${type}/${id}/actions/${finishType}/`, payload)
            .then(response => {
                return path.success(response)
            })
            .catch(response => {
                return path.error(response)
            })
    }
}
