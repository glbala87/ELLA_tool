import { Module } from 'cerebral'

import { initApp, authenticate } from '../../../common/factories'
import importModule from './import'
import changeView from '../factories/changeView'
import routed from './signals/routed'
import collapseChanged from './signals/collapseChanged'
import updateOverviewTriggered from './signals/updateOverviewTriggered'
import finalizedPageChanged from './signals/finalizedPageChanged'
import redirectToSection from './actions/redirectToSection'
import setSections from './actions/setSections'
import loadOverviewState from './actions/loadOverviewState'

const routedWithSectionSequence = initApp(authenticate([changeView('overview'), routed]))
const routedSequence = initApp(
    authenticate([changeView('overview'), setSections, loadOverviewState, redirectToSection])
)

export default Module({
    modules: {
        import: importModule
    },
    state: {}, // State set in changeView
    signals: {
        collapseChanged,
        finalizedPageChanged,
        updateOverviewTriggered,
        routedWithSection: routedWithSectionSequence,
        routed: routedSequence
    }
})
