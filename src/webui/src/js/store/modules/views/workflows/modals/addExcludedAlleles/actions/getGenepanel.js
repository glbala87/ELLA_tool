export default function getGenepanel({ http, path, state }) {
    const id = state.get('views.workflows.id')
    const genepanel = state.get('views.workflows.modals.addExcludedAlleles.genepanel')
    const alleleIds = state
        .get('views.workflows.modals.addExcludedAlleles.viewAlleleIds')
        .concat(state.get('views.workflows.modals.addExcludedAlleles.includedAlleleIds'))

    if (!alleleIds.length) {
        return path.success({ result: [] })
    }

    return http
        .get(`workflows/analyses/${id}/genepanels/${genepanel.name}/${genepanel.version}/`, {
            allele_ids: alleleIds.join(',')
        })
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
