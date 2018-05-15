export function getAddedState() {
    return {
        selectedPage: 1,
        perPage: 5,
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
        perPage: 5,
        filter: '',
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
            genepanel: null // Currently selected genepanel
        },
        selectedGenepanel: null,
        candidates: getCandidatesState(),
        added: getAddedState()
    }
}