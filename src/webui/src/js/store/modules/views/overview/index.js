import { Module } from 'cerebral'

import changeSection from './signals/changeSection'
import routed from './signals/routed'
import { initApp, authenticate } from '../../../common/factories'
import changeView from '../factories/changeView'

export default Module({
    state: {}, // State set in changeView
    signals: {
        changeSection,
        routed: initApp(authenticate([changeView('overview'), routed]))
    }
})
