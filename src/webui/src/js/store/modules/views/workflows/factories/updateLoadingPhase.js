export default function updateLoadingPhase(phase) {
    return function setLoadingText({ state }) {
        const workflowType = state.get('views.workflows.type')
        const workflowStats = state.get('views.workflows.data.stats')

        let numTotalAlleles = 0
        if (workflowStats && 'allele_count' in workflowStats) {
            numTotalAlleles = workflowStats.allele_count
        }

        let showLoadingText = numTotalAlleles > 100 && workflowType === 'analysis'
        let loaded = false
        let loadingText = ''

        if (phase === 'start') {
            loadingText = ''
        } else if (phase === 'filtering') {
            if (showLoadingText) {
                loadingText = `Filtering ${numTotalAlleles} variants`
            }
        } else if (phase === 'variants') {
            if (showLoadingText) {
                const numVariants = state.get('views.workflows.interpretation.selected.allele_ids')
                    .length
                loadingText = `Loading ${numVariants} variants`
            }
        } else if (phase === 'done') {
            loaded = true
        } else {
            throw Error(`Invalid loading phase ${phase}`)
        }

        state.set(`views.workflows.loaded`, loaded)
        state.set(`views.workflows.loadingText`, loadingText)
    }
}
