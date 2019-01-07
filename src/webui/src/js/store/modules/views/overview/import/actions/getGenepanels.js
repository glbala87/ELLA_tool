export default function getGenepanels({ http, path }) {
    return http
        .get('genepanels/')
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.log(error)
            return path.error(error)
        })
}
