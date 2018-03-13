const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function getGenepanels({ http, path, state }) {
    let type = TYPES[state.get('views.workflows.type')]
    let id = state.get('views.workflows.id')

    return http
        .get(`workflows/${type}/${id}/genepanels/`)
        .then(response => {
            return path.success({ result: response.result })
        })
        .catch(response => {
            return path.error({ result: response.result })
        })
}
