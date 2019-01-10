function getSelectedFilterResults({ http, path, state }) {
    const type = state.get('views.workflows.type')

    if (type === 'analysis') {
        const selectedInterpretationId = state.get('views.workflows.interpretation.selected.id')
        const analysisId = state.get('views.workflows.id')
        let filterconfigId = state.get(
            'views.workflows.interpretation.selected.state.filterconfigId'
        )
        let current = state.get('views.workflows.interpretation.selected.current') || false
        let resource = `workflows/analyses/${analysisId}/interpretations/${selectedInterpretationId}/filteredalleles/?filterconfig_id=${filterconfigId}&current=${current}`
        return http
            .get(resource)
            .then((response) => {
                return path.success({
                    allele_ids: response.result.allele_ids,
                    excluded_allele_ids: response.result.excluded_allele_ids
                })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    } else {
        return path.success({ result: null })
    }
}

export default getSelectedFilterResults
