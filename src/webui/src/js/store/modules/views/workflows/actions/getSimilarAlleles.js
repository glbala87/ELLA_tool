import processAlleles from '../../../../common/helpers/processAlleles'

function getSimilarAlleles({ http, path, state }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const genepanel = state.get('views.workflows.interpretation.data.genepanel')
    const aIds = Object.keys(alleles)

    if (Object.keys(alleles).length) {
        return http
            .get(`workflows/similar_alleles/${genepanel.name}/${genepanel.version}/`, {
                allele_ids: aIds.join(',')
            })
            .then((response) => {
                const similar_alleles = response.result
                for (let allele_id of Object.keys(similar_alleles)) {
                    processAlleles(similar_alleles[allele_id], genepanel)
                }
                return path.success({ result: similar_alleles })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    } else {
        return path.success({ result: {} })
    }
}

export default getSimilarAlleles
