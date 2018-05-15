function checkConfirmPassword({ state }) {
    let match = state.get('views.login.newPassword') === state.get('views.login.confirmNewPassword')
    if (state.get('views.login.confirmNewPassword').length) {
        state.set('views.login.passwordMatches', match)
    }
}

export default checkConfirmPassword
