const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function getGenepanel({ http, path, props, state }) {
    const type = TYPES[state.get('views.workflows.type')]
    const id = state.get('views.workflows.id')
    const selectedGenepanel = state.get('views.workflows.selectedGenepanel')

    return http
        .get(
            `workflows/${type}/${id}/genepanels/${selectedGenepanel.name}/${
                selectedGenepanel.version
            }/`
        )
        .then(response => {
            return path.success({ result: response.result })
        })
        .catch(response => {
            return path.error({ result: response.result })
        })
}
