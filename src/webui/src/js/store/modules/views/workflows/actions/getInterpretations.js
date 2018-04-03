const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getInterpretations({ http, path, state }) {
    let type = TYPES[state.get('views.workflows.type')]
    let id = state.get('views.workflows.id')
    return http
        .get(`workflows/${type}/${id}/interpretations/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getInterpretations
