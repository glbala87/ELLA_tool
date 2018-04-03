import getAlleleAssessment from '../computed/getAlleleAssessment'

export default function getSuggestedClassification({ http, resolve, path, props }) {
    const { alleleId } = props
    const alleleAssessment = resolve.value(getAlleleAssessment(alleleId))
    if (!alleleAssessment) {
        return path.success({ result: { class: null } })
    }
    const codes = alleleAssessment.evaluation.acmg.included.map((c) => c.code)
    if (!codes || !codes.length) {
        return path.success({ result: { class: null } })
    }

    // Abort any in-flight queries
    http.abort('acmg/classifications*')

    return http
        .get('acmg/classifications/', { codes: codes.join(',') })
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            if (error.isAborted) {
                return path.aborted()
            }
            console.error(error)
            return path.error(error)
        })
}
