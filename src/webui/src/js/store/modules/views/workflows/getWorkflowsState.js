import getAlleleSidebarState from './alleleSidebar/getAlleleSidebarState'
import getInterpretationState from './interpretation/getInterpretationState'
import getWorkLogState from './worklog/getWorkLogState'

export default function getWorkflowsState() {
    // We must handle modules state in here due to changeView resetting it
    return {
        alleleSidebar: getAlleleSidebarState(),
        components: null, // Set in prepareComponents
        data: {
            // Data from backend
            collisions: null,
            interpretations: null,
            interpretationlogs: null,
            stats: null
        },
        modals: {
            addExcludedAlleles: {
                show: false
            },
            genepanelOverview: {
                show: false
            },
            reassignWorkflow: {
                show: false
            },
            finishConfirmation: {
                show: false
            },
            addExternal: {
                show: false
            },
            addPrediction: {
                show: false
            },
            addReferences: {
                show: false
            }
        },
        id: null, // analysis id or allele id
        interpretation: getInterpretationState(),
        loaded: false, // Whether view should render
        selectedAllele: null, // id of selected allele
        selectedComponent: null, // Set in prepareComponents
        type: null, // 'analysis' or 'allele'
        worklog: getWorkLogState()
    }
}
