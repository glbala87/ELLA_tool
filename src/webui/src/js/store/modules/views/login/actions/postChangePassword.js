export default function postChangePassword({ http, path, state }) {
    let payload = {
        username: state.get('views.login.username'),
        password: state.get('views.login.password'),
        new_password: state.get('views.login.newPassword')
    }
    return http
        .post('users/actions/changepassword/', payload)
        .then((response) => {
            return path.success(response)
        })
        .catch((response) => {
            console.error(response)
            return path.error({ errorMessage: response.response.result.message })
        })
}
