import { Module } from 'cerebral'

import routed from './signals/routed'
import { initApp } from '../../../common/factories'
import changeView from '../factories/changeView'
import loginClicked from './signals/loginClicked'
import modeChanged from './signals/modeChanged'
import usernameChanged from './signals/usernameChanged'
import passwordChanged from './signals/passwordChanged'
import newPasswordChanged from './signals/newPasswordChanged'
import confirmNewPasswordChanged from './signals/confirmNewPasswordChanged'
import reset from './actions/reset'

export default Module({
    state: {}, // State set in changeView
    signals: {
        routed: initApp([changeView('login'), routed]),
        modeChanged,
        usernameChanged,
        passwordChanged,
        newPasswordChanged,
        confirmNewPasswordChanged,
        loginClicked,
        reset: [reset]
    }
})
