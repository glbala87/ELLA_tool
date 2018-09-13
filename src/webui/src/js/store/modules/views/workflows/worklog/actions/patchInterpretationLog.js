const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function patchInterpretationLog({ state, props, http, path }) {
    const { interpretationLog } = props

    const type = state.get('views.workflows.type')
    const postType = TYPES[type]
    const id = state.get('views.workflows.id')

    const payload = {
        message: interpretationLog.message
    }
    const logId = interpretationLog.id

    return http
        .patch(`workflows/${postType}/${id}/logs/${logId}/`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}
