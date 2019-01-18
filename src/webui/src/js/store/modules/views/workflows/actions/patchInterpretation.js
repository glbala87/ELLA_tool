import getSelectedInterpretation from '../computed/getSelectedInterpretation'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function patchInterpretation({ state, http, path, resolve }) {
    const type = TYPES[state.get('views.workflows.type')]
    const id = state.get('views.workflows.id')
    const interpretation = resolve.value(getSelectedInterpretation)

    if (interpretation.status !== 'Ongoing') {
        throw Error('Trying to save when interpretation status is not Ongoing')
    }

    const currentState = state.get('views.workflows.interpretation.state')
    const currentUserState = state.get('views.workflows.interpretation.userState')
    const selectedId = state.get('views.workflows.interpretation.selectedId')

    const payload = {
        id: selectedId,
        state: currentState,
        user_state: currentUserState
    }
    return http
        .patch(`workflows/${type}/${id}/interpretations/${interpretation.id}/`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            console.error(response)
            return path.error({ response: response.response })
        })
}

export default patchInterpretation
