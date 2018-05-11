export default function getSamples({ http, path, props }) {
    const { term } = props
    return http
        .get(`import/service/samples/`, { term })
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.log(error)
            return path.error(error)
        })
}
