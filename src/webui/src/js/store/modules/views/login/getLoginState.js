const MODES = ['Login', 'Change password']

export default function getLoginState() {
    return {
        username: '',
        password: '',
        newPassword: '',
        confirmNewPassword: '',
        modes: MODES,
        mode: MODES[0],
        passwordChecks: [],
        passwordMatches: true,
        passwordStrength: true
    }
}
