import processAlleles from '../../../../../../common/helpers/processAlleles'

export default function({ http, path, state, props }) {
    const { alleleIds } = props
    const analysisId = state.get('views.workflows.modals.addExcludedAlleles.analysisId')
    const selectedInterpretation = state.get(
        'views.workflows.modals.addExcludedAlleles.selectedInterpretation'
    )
    const selectedInterpretationId = state.get(
        'views.workflows.modals.addExcludedAlleles.selectedInterpretationId'
    )
    const genepanel = state.get('views.workflows.modals.addExcludedAlleles.data.genepanel')
    const filterConfigId = state.get('views.workflows.modals.addExcludedAlleles.filterconfig.id')

    if (!alleleIds.length) {
        return path.success({ result: [] })
    }
    return http
        .get(
            `workflows/analyses/${analysisId}/interpretations/${selectedInterpretation.id}/alleles`,
            {
                allele_ids: alleleIds.join(','),
                filterconfig_id: filterConfigId,
                current: selectedInterpretationId === 'current'
            }
        )
        .then((response) => {
            processAlleles(response.result, genepanel)
            const result = response.result.reduce((obj, allele) => {
                obj[allele.id] = allele
                return obj
            }, {})
            return path.success({ result: result })
        })
        .catch((err) => {
            console.error(err)
            return path.error({ result: err })
        })
}
