const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getCollisions({ http, path, state }) {
    let type = TYPES[state.get('views.workflows.type')]
    let id = state.get('views.workflows.id')
    let alleles = state.get('views.workflows.interpretation.data.alleles')
    if (!alleles) {
        return path.success({ result: [] })
    }
    let allele_ids = Object.keys(alleles)

    return http
        .get(`workflows/${type}/${id}/collisions/`, { allele_ids: allele_ids.join(',') })
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((err) => {
            console.error(err)
            return path.error({ result: err })
        })
}

export default getCollisions
