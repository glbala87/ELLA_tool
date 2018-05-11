function reset({ state }) {
    let min_length = state.get('app.config')['user']['auth']['password_minimum_length']
    let password_checks = [[`Minimum ${min_length} letters`, false]]

    for (let s of state.get('app.config')['user']['auth']['password_match_groups_descr']) {
        password_checks.push([s, false])
    }
    state.set('views.login.passwordChecks', password_checks)
    state.set(
        'views.login.passwordChecksRequired',
        state.get('app.config')['user']['auth']['password_num_match_groups']
    )
}

export default reset
