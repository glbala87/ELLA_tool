import processAlleles from '../../../../common/helpers/processAlleles'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getCollisions({ http, path, props, state }) {
    const config = state.get('app.config')
    let type = TYPES[state.get('views.workflows.type')]
    let id = state.get('views.workflows.id')
    let alleles = state.get('views.workflows.data.alleles')
    if (!alleles) {
        return path.success({ result: [] })
    }
    let allele_ids = Object.keys(alleles)

    return http
        .get(`workflows/${type}/${id}/collisions/`, { allele_ids: allele_ids.join(',') })
        .then((response) => {
            for (let d of response.result) {
                processAlleles([d.allele], config)
            }
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getCollisions
