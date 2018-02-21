import { Module } from 'cerebral'

import { initApp, authenticate } from '../../../common/factories'
import changeView from '../factories/changeView'
import routed from './signals/routed'
import logoutClicked from './signals/logoutClicked'

export default Module({
    state: {}, // State set in changeView
    signals: {
        logoutClicked,
        routed: initApp(authenticate([changeView('dashboard'), routed]))
    }
})
