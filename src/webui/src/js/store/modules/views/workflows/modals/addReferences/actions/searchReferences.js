import processReferences from '../../../../../../common/helpers/processReferences'

export default ({ state, props, http, path }) => {
    let { value, perPage } = props
    if (value.length < 3) {
        return path.success({ result: [] })
    }
    return http
        .get('references/', {
            s: JSON.stringify({ search_string: value }),
            per_page: perPage ? perPage : null
        })
        .then((response) => {
            processReferences(response.result)
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
