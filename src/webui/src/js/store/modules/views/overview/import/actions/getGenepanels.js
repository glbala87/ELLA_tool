export default function getGenepanels({ state, http, path }) {
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
