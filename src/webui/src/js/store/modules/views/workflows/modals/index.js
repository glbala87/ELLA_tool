import { Module } from 'cerebral'
import addExcludedAlleles from './addExcludedAlleles'
import finishConfirmation from './finishConfirmation'
import genepanelOverview from './genepanelOverview'
import reassignWorkflow from './reassignWorkflow'

export default Module({
    state: {
        // State would be replaced by getWorkflowState(),
        // use that if you need initial state
    },
    signals: {},
    modules: {
        addExcludedAlleles,
        finishConfirmation,
        genepanelOverview,
        reassignWorkflow
    }
})
