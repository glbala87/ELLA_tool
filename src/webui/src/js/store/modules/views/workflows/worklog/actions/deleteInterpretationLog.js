const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function deleteInterpretationLog({ state, props, http, path }) {
    const type = state.get('views.workflows.type')
    const postType = TYPES[type]
    const workflowId = state.get('views.workflows.id')

    const logId = props.id

    return http
        .delete(`workflows/${postType}/${workflowId}/logs/${logId}/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}
