import { Module } from 'cerebral'

import sectionChanged from './signals/sectionChanged'
import { initApp, authenticate } from '../../../common/factories'
import importModule from './import'
import changeView from '../factories/changeView'
import routed from './signals/routed'
import collapseChanged from './signals/collapseChanged'
import updateImportJobCountTriggered from './signals/updateImportJobCountTriggered'
import updateOverviewTriggered from './signals/updateOverviewTriggered'
import showImportModalClicked from './signals/showImportModalClicked'
import finalizedPageChanged from './signals/finalizedPageChanged'

export default Module({
    modules: {
        import: importModule
    },
    state: {}, // State set in changeView
    signals: {
        collapseChanged,
        finalizedPageChanged,
        sectionChanged,
        updateImportJobCountTriggered,
        updateOverviewTriggered,
        routed: initApp(authenticate([changeView('overview'), routed])),
        showImportModalClicked
    }
})
