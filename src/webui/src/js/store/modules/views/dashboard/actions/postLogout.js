function postLogout({ http, path, state }) {
    return http
        .post('users/actions/logout/', {})
        .then(response => {
            return path.success(response)
        })
        .catch(response => {
            return path.error(response)
        })
}

export default postLogout
