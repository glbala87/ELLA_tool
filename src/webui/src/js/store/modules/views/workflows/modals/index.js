import { Module } from 'cerebral'
import addExcludedAlleles from './addExcludedAlleles'
import alleleHistory from './alleleHistory'
import finishConfirmation from './finishConfirmation'
import genepanelOverview from './genepanelOverview'
import reassignWorkflow from './reassignWorkflow'
import addPrediction from './addPrediction'
import addExternal from './addExternal'
import addReferences from './addReferences'
import evaluateReference from './evaluateReference'

export default Module({
    state: {
        // State would be replaced by getWorkflowState(),
        // use that if you need initial state
    },
    signals: {},
    modules: {
        addExcludedAlleles,
        alleleHistory,
        finishConfirmation,
        genepanelOverview,
        reassignWorkflow,
        addPrediction,
        addExternal,
        addReferences,
        evaluateReference
    }
})
