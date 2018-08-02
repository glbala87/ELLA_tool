import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './login.ngtmpl.html'

app.component('login', {
    templateUrl: 'login.ngtmpl.html',
    controller: connect(
        {
            usernameChanged: signal`views.login.usernameChanged`,
            passwordChanged: signal`views.login.passwordChanged`,
            newPasswordChanged: signal`views.login.newPasswordChanged`,
            confirmNewPasswordChanged: signal`views.login.confirmNewPasswordChanged`,
            changePasswordClicked: signal`views.login.changePasswordClicked`,
            modeChanged: signal`views.login.modeChanged`,
            loginClicked: signal`views.login.loginClicked`,
            username: state`views.login.username`,
            password: state`views.login.password`,
            newPassword: state`views.login.newPassword`,
            confirmNewPassword: state`views.login.confirmNewPassword`,
            passwordChecks: state`views.login.passwordChecks`,
            passwordChecksRequired: state`views.login.passwordChecksRequired`,
            passwordMatches: state`views.login.passwordMatches`,
            passwordStrength: state`views.login.passwordStrength`,
            modes: state`views.login.modes`,
            mode: state`views.login.mode`
        },
        'Login'
    )
})
