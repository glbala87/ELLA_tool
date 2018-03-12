import { Module } from 'cerebral'

import changeSection from './signals/changeSection'
import { initApp, authenticate } from '../../../common/factories'
import changeView from '../factories/changeView'
import routed from './signals/routed'
import collapseChanged from './signals/collapseChanged'

export default Module({
    state: {}, // State set in changeView
    signals: {
        collapseChanged,
        changeSection,
        routed: initApp(authenticate([changeView('overview'), routed]))
    }
})
