function getAllUsers({ http, path }) {
    return http
        .get(`users/`)
        .then((response) => {
            if (response.status === 200) {
                return path.success(response)
            }
            return path.error({ result: response.result })
        })
        .catch((r) => {
            return path.error(r)
        })
}

export default getAllUsers