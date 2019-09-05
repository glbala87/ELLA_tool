export default function getGenepanelStats({ http, path, props }) {
    const { name, version } = props

    return http
        .get(`genepanels/${name}/${version}/stats/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((err) => {
            console.error(err)
            return path.error({ result: err })
        })
}
