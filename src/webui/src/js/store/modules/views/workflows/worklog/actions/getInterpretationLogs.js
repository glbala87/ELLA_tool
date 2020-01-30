const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function getInterpretations({ http, path, state }) {
    let type = TYPES[state.get('views.workflows.type')]
    let id = state.get('views.workflows.id')
    return http
        .get(`workflows/${type}/${id}/logs/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((err) => {
            console.error(err)
            return path.error({ error: err })
        })
}
