export default function getAnalysesForAllele({ http, props, path }) {
    return http
        .get(`alleles/${props.alleleId}/analyses/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error(response)
        })
}
