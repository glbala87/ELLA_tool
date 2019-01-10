export default function({ http, props, path }) {
    let filterconfigId = props.filterconfigId

    return http
        .get(`filterconfigs/${filterconfigId}`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
