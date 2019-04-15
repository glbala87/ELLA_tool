const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function(startType) {
    return function startWorkflow({ state, http, path }) {
        const type = TYPES[state.get('views.workflows.type')]
        const id = state.get('views.workflows.id')
        const genepanel = state.get('views.workflows.interpretation.data.genepanel')

        if (!['start', 'reopen', 'override'].find((e) => e === startType)) {
            console.error(`'Invalid startType ${startType}`)
            return path.error()
        }

        let payload = {}
        if (startType === 'start') {
            payload = {
                gp_name: genepanel.name,
                gp_version: genepanel.version
            }
        }

        return http
            .post(`workflows/${type}/${id}/actions/${startType}/`, payload)
            .then((response) => {
                return path.success(response)
            })
            .catch((response) => {
                return path.error(response)
            })
    }
}
