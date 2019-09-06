import getSelectedInterpretation from '../computed/getSelectedInterpretation'

function getFilteredAlleles({ http, path, state, resolve }) {
    const type = state.get('views.workflows.type')

    if (type === 'analysis') {
        const selectedInterpretation = resolve.value(getSelectedInterpretation)
        const analysisId = state.get('views.workflows.id')

        // Run filter if current is true
        let params = {}
        let current = state.get('views.workflows.interpretation.selectedId') === 'current'
        let isDone = selectedInterpretation.status === 'Done'
        if (current || !isDone) {
            params['filterconfig_id'] = state.get(
                'views.workflows.interpretation.state.filterconfigId'
            )
        }

        return http
            .get(
                `workflows/analyses/${analysisId}/interpretations/${selectedInterpretation.id}/filteredalleles/`,
                params
            )
            .then((response) => {
                return path.success({ result: response.result })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    } else {
        return path.success({
            result: {
                allele_ids: [state.get('views.workflows.id')],
                excluded_allele_ids: null
            }
        })
    }
}

export default getFilteredAlleles
