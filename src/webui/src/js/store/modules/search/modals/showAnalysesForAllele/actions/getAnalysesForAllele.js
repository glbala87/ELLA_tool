import processAnalyses from '../../../../../common/helpers/processAnalyses'

export default function getAnalysesForAllele({ http, props, path }) {
    return http
        .get(`alleles/${props.alleleId}/analyses/`)
        .then((response) => {
            processAnalyses(response.result)
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error(response)
        })
}
