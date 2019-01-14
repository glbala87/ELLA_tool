function getFilteredAlleles({ http, path, state }) {
    const type = state.get('views.workflows.type')

    if (type === 'analysis') {
        const selectedInterpretationId = state.get('views.workflows.interpretation.selected.id')
        const analysisId = state.get('views.workflows.id')

        // Run filter if current is true
        let params = {}

        // TODO: Hackish. Fixme.
        let current = state.get('views.workflows.interpretation.selected.current') || false
        let isOngoing = state.get('views.workflows.interpretation.isOngoing')
        let notStarted =
            state.get('views.workflows.interpretation.selected.status') === 'Not started'

        if (current || isOngoing || notStarted) {
            params['filterconfig_id'] = state.get(
                'views.workflows.interpretation.selected.state.filterconfigId'
            )
        }
        console.log(params)
        return http
            .get(
                `workflows/analyses/${analysisId}/interpretations/${selectedInterpretationId}/filteredalleles/`,
                params
            )
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
        return path.success({
            allele_ids: [state.get('views.workflows.id')],
            excluded_allele_ids: null
        })
    }
}

export default getFilteredAlleles
