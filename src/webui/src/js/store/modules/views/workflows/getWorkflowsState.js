import getAlleleSidebarState from './alleleSidebar/getAlleleSidebarState'
import getInterpretationState from './interpretation/getInterpretationState'

export default function getWorkflowsState() {
    // We must handle modules state in here due to changeView resetting it
    return {
        alleleSidebar: getAlleleSidebarState(),
        collisions: null,
        components: null, // Set in prepareComponents
        data: {
            // Data from backend
            alleles: null,
            references: null,
            attachments: null,
            collisions: null,
            interpretations: null,
            interpretationlogs: null
        },
        historyInterpretations: null, // Holds data for choosing what interpretation to view
        id: null, // analysis id or allele id
        interpretation: getInterpretationState(),
        loaded: false, // Whether view should render
        modals: {
            addExcludedAlleles: {
                show: false,
                data: {},
                totalCount: null,
                numPerPage: 2,
                currentPage: 1,
                geneOptions: [],
                showAlleleIds: [] // Holds ids for current view selection
                //categories: [continue here!]
            }
        },
        selectedAllele: null, // id of selected allele
        selectedComponent: null, // Set in prepareComponents
        type: null // 'analysis' or 'allele'
    }
}
