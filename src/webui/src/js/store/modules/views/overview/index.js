import { Module } from 'cerebral'

import sectionChanged from './signals/sectionChanged'
import { initApp, authenticate } from '../../../common/factories'
import changeView from '../factories/changeView'
import routed from './signals/routed'
import collapseChanged from './signals/collapseChanged'
import updateImportJobCountTriggered from './signals/updateImportJobCountTriggered'
import updateOverviewTriggered from './signals/updateOverviewTriggered'
import showImportModalClicked from './signals/showImportModalClicked'

export default Module({
    state: {}, // State set in changeView
    signals: {
        collapseChanged,
        sectionChanged,
        updateImportJobCountTriggered,
        updateOverviewTriggered,
        routed: initApp(authenticate([changeView('overview'), routed])),
        showImportModalClicked
    }
})
