import getImportState from './import/getImportState'

export let AVAILABLE_SECTIONS = {
    // All possible sections
    variants: {
        displayName: 'Variants',
        selected: false,
        finalized: {
            selectedPage: 1
        }
    },
    analyses: {
        displayName: 'Analyses',
        selected: false,
        finalized: {
            selectedPage: 1
        }
    },
    'analyses-by-classified': {
        displayName: 'Analyses',
        selected: false,
        finalized: {
            selectedPage: 1
        }
    },
    import: {
        displayName: 'Import',
        selected: false
    }
}

export default function getOverviewState() {
    return {
        sectionKeys: [], // Decided by user's config
        sections: {},
        state: {},
        data: {
            alleles: null,
            allelesFinalized: null,
            analyses: null,
            analysesFinalized: null
        },
        import: getImportState(),
        importJobsStatus: {}
    }
}
