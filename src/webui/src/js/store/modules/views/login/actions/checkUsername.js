function checkUsername({ state, path, toastr }) {
    let username = state.get('views.login.username')
    if (username.length > 0 && !username.contains(' ')) {
        return path.pass()
    } else {
        return path.fail()
    }
}

export default checkUsername