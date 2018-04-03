export default function getUserStats({ http, path, state }) {
    return http
        .get('overviews/userstats/')
        .then((response) => {
            return path.success(response)
        })
        .catch((response) => {
            return path.error(response)
        })
}
