export default function getAllUsers({ http, path }) {
    return http
        .get(`users/`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((err) => {
            console.error(err)
            return path.error(err)
        })
}
