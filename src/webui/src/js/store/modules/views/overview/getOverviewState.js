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
    'analyses-by-findings': {
        displayName: 'Analyses',
        selected: false,
        finalized: {
            selectedPage: 1
        }
    }
}

export default function getOverviewState() {
    return {
        sectionKeys: [], // Decided by user's config
        sections: {},
        data: {
            alleles: null,
            allelesFinalized: null,
            analyses: null,
            analysesFinalized: null
        }
    }
}
