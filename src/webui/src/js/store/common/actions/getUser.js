function getUser({ http, path }) {
    return http
        .get(`users/currentuser/`)
        .then(response => {
            if (response.status === 200) {
                return path.success(response)
            }
            return path.error({ result: response.result })
        })
        .catch(r => {
            return path.error(r)
        })
}

export default getUser
