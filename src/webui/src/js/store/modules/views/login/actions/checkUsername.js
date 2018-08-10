function checkUsername({ state, path }) {
    let username = state.get('views.login.username')
    if (username.length > 0 && !username.includes(' ')) {
        return path.pass()
    } else {
        return path.fail()
    }
}

export default checkUsername
