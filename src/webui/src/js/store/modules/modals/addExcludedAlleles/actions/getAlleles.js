import processAlleles from '../../../../common/helpers/processAlleles'

export default function({ http, path, state, props }) {
    const { alleleIds } = props
    const config = state.get('app.config')
    const analysisId = state.get('modals.addExcludedAlleles.analysisId')
    const genepanel = state.get('modals.addExcludedAlleles.data.genepanel')
    if (!alleleIds.length) {
        return path.success({ result: [] })
    }
    return http
        .get(`alleles/`, {
            q: JSON.stringify({ id: alleleIds }),
            analysis_id: analysisId,
            gp_name: genepanel.name,
            gp_version: genepanel.version
        })
        .then((response) => {
            processAlleles(response.result, config, genepanel)
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
