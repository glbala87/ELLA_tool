const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function postInterpretationLog({ state, props, http, path }) {
    const { interpretationLog } = props

    const type = state.get('views.workflows.type')
    const postType = TYPES[type]
    const id = state.get('views.workflows.id')

    console.log(interpretationLog)
    return http
        .post(`workflows/${postType}/${id}/logs/`, interpretationLog)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}
