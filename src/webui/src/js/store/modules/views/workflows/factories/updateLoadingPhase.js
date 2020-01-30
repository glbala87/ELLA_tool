import getAlleleIdsFromInterpretation from '../computed/getAlleleIdsFromInterpretation'

export default function updateLoadingPhase(phase) {
    return function setLoadingText({ state, resolve }) {
        const workflowType = state.get('views.workflows.type')
        const workflowStats = state.get('views.workflows.data.stats')

        let numTotalAlleles = 0
        if (workflowStats && 'allele_count' in workflowStats) {
            numTotalAlleles = workflowStats.allele_count
        }

        let showLoadingText = numTotalAlleles > 100 && workflowType === 'analysis'
        let loaded = false
        let loadingWorkflow = {
            filteringAlleles: null,
            loadingAlleles: null
        }

        if (phase === 'start') {
            loadingWorkflow = {
                filteringAlleles: null,
                loadingAlleles: null
            }
        } else if (phase === 'filtering') {
            if (showLoadingText) {
                loadingWorkflow = {
                    filteringAlleles: numTotalAlleles,
                    loadingAlleles: null
                }
            }
        } else if (phase === 'variants') {
            if (showLoadingText) {
                const numVariants = resolve.value(getAlleleIdsFromInterpretation).length
                loadingWorkflow = {
                    filteringAlleles: null,
                    loadingAlleles: numVariants
                }
            }
        } else if (phase === 'done') {
            loadingWorkflow = {
                filteringAlleles: null,
                loadingAlleles: null
            }
            loaded = true
        } else {
            throw Error(`Invalid loading phase ${phase}`)
        }

        state.set(`views.workflows.loaded`, loaded)
        state.set(`views.workflows.loadingWorkflow`, loadingWorkflow)
    }
}
