export default function getSamples({ http, path, props }) {
    const { term, limit } = props
    return http
        .get(`import/service/samples/`, { term, limit })
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.log(error)
            return path.error(error)
        })
}
