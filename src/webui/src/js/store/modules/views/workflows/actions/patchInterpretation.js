const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function patchInterpretation({ state, http, path }) {
    const type = TYPES[state.get('views.workflows.type')]
    const id = state.get('views.workflows.id')
    const interpretation = state.get('views.workflows.interpretation.selected')

    if (interpretation.status !== 'Ongoing') {
        throw Error('Trying to save when interpretation status is not Ongoing')
    }

    const payload = {
        id: interpretation.id,
        state: interpretation.state,
        user_state: interpretation.user_state
    }

    return http
        .patch(`workflows/${type}/${id}/interpretations/${interpretation.id}/`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default patchInterpretation
