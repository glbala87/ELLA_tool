import processAlleles from '../../../../common/helpers/processAlleles'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getCollisions({ http, path, props, state }) {
    let type = TYPES[state.get('views.workflows.type')]
    let id = state.get('views.workflows.id')
    return http
        .get(`workflows/${type}/${id}/collisions/`)
        .then((response) => {
            for (let d of response.result) {
                processAlleles([d.allele])
            }
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getCollisions
