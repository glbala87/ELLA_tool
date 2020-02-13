export default async function postLogin({ http, path, state }) {
    let payload = {
        username: state.get('views.login.username'),
        password: state.get('views.login.password')
    }
    try {
        const response = await http.post('login', payload)
        return path.success(response)
    } catch (err) {
        console.error(err)
        return path.error({ errorMessage: `Login unsuccessful: ${err.response.result.message}` })
    }
}
