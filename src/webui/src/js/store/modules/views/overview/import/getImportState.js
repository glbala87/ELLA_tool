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
        importSourceType: 'user',
        sample: {
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
                added: getAddedState(),
                selectedImportUserGroups: []
            },
            importHistoryPage: 1,

            selectedGenepanel: null,
            candidates: getCandidatesState(),
            added: getAddedState(),
            priority: 1
        },
        user: {
            jobData: [
                {
                    parsedInput: {
                        header: '',
                        variantDataLines: [
                            {
                                display: '13-32890572-G-A (het)',
                                value: '13-32890572-G-A (het)',
                                hasGenotype: true
                            }
                        ]
                    },
                    selection: {
                        type: 'Analysis',
                        mode: 'Create',
                        technology: 'Sanger',
                        priority: 1,
                        analysis: null,
                        analysisName: '',
                        genepanel: null,
                        include: [true]
                    },
                    collapsed: true
                },
                {
                    parsedInput: {
                        header: '',
                        variantDataLines: [
                            {
                                display: '13-32890587-C-T (homo)',
                                value: '13-32890587-C-T (homo)',
                                hasGenotype: true
                            }
                        ]
                    },
                    selection: {
                        type: 'Analysis',
                        mode: 'Create',
                        technology: 'Sanger',
                        priority: 1,
                        analysis: null,
                        analysisName: '',
                        genepanel: null,
                        include: [true]
                    },
                    collapsed: false
                }
            ]
        }
    }
}
