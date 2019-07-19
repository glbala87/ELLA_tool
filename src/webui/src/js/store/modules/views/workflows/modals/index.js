import { Module } from 'cerebral'
import addExcludedAlleles from './addExcludedAlleles'
import alleleAssessmentHistory from './alleleAssessmentHistory'
import finishConfirmation from './finishConfirmation'
import reassignWorkflow from './reassignWorkflow'

export default Module({
    state: {
        // State would be replaced by getWorkflowState(),
        // use that if you need initial state
    },
    signals: {},
    modules: {
        addExcludedAlleles,
        alleleAssessmentHistory,
        finishConfirmation,
        reassignWorkflow
    }
})
