function checkPasswordStrength({ props, path, state }) {
    let pw = props.newPassword
    let group_matches = 0
    let groups = state.get('app.config')['users']['password_match_groups']
    let num_match_groups = state.get('app.config')['users']['password_num_match_groups']
    let min_length = state.get('app.config')['users']['password_minimum_length']

    let criterias = state.get('views.login.passwordChecks')

    criterias[0][1] = pw.length >= min_length

    for (let i in groups) {
        let g = groups[i]
        let r = new RegExp(g)
        let test = r.test(pw)
        criterias[parseInt(i) + 1][1] = test
        group_matches += test
    }

    // Explicitly update state, even though we mutated object
    state.set('views.login.passwordChecks', criterias)
    let pass = group_matches >= num_match_groups && pw.length >= min_length

    state.set('views.login.passwordStrength', pass)
}

export default checkPasswordStrength
