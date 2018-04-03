export default function getOptions({ http, props, path }) {
    return http
        .get(`search/options?q=${encodeURIComponent(JSON.stringify(props.options))}`)
        .then((response) => {
            return path.success(response)
        })
        .catch((response) => {
            return path.error(response)
        })
}
