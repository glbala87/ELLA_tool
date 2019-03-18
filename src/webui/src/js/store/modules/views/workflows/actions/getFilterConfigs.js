function getFilterConfigs({ http, path, state }) {
    const type = state.get('views.workflows.type')
    if (type === 'analysis') {
        const analysisId = state.get('views.workflows.id')
        return http
            .get(`workflows/analyses/${analysisId}/filterconfigs`)
            .then((response) => {
                return path.success({ result: response.result })
            })
            .catch((response) => {
                return path.error({ message: response.response.result.message })
            })
    } else {
        return path.success({ result: null })
    }
}

export default getFilterConfigs
