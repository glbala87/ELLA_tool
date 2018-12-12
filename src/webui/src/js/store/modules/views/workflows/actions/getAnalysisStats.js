export default function getAnalysisStats({ http, path, props }) {
    return http
        .get(`workflows/analyses/${props.analysisId}/stats/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
