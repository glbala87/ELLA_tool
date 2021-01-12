import processReferences from '../../../../../../common/helpers/processReferences'

export default ({ http, props, path }) => {
    const { data } = props
    return http
        .post('references/', data)
        .then((response) => {
            processReferences([response.result])
            return path.success({ refId: response.result.id, reference: response.result })
        })
        .catch((response) => {
            return path.error({ error: response.result })
        })
}
