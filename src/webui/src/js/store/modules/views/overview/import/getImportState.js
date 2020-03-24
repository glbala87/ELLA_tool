export function getAddedState() {
    return {
        selectedPage: 1,
        perPage: 8,
        filter: '',
        addedGenepanel: {
            genes: {}, // Use object for fast lookup
            name: null,
            version: null,
            config: {}
        },
        filteredGenepanel: null,
        filteredFlattened: null
    }
}

export function getCandidatesState() {
    return {
        selectedPage: 1,
        filter: '',
        perPage: 8,
        filterBatch: '',
        filterBatchProcessed: false,
        filteredFlattened: null,
        filteredGenepanel: null
    }
}

export default function getImportState() {
    return {
        sampleQuery: '',
        customGenepanel: false,
        data: {
            samples: null, // Sample results
            genepanels: null, // Available genepanels
            genepanel: null, // Currently selected genepanel
            activeImportJobs: null,
            importJobsHistory: null
        },
        custom: {
            selectedFilterMode: 'single',
            candidates: getCandidatesState(),
            added: getAddedState()
        },
        importHistoryPage: 1,
        importSourceType: 'user',
        selectedGenepanel: null,
        candidates: getCandidatesState(),
        added: getAddedState(),
        priority: 1
    }
}
