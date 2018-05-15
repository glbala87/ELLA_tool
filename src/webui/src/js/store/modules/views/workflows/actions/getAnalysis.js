function getAnalysis({ http, path, props }) {
    return http
        .get(`analyses/${props.analysisId}/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getAnalysis
