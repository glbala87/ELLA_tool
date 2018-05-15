function postLogin({ http, path, state }) {
    let payload = {
        username: state.get('views.login.username'),
        password: state.get('views.login.password')
    }
    return http
        .post('users/actions/login/', payload)
        .then((response) => {
            return path.success(response)
        })
        .catch((response) => {
            return path.error({ errorMessage: `Login unsuccessful: ${response.response.result}` })
        })
}

export default postLogin
