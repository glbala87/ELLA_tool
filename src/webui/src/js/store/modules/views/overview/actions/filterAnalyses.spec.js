import { runAction } from 'cerebral/test'

import { filterAnalyses, withinRange, createDate } from './filterAnalyses'
import { DEFAULT_FILTER } from '../getOverviewState'

describe('filterAnalyses', function() {
    it('default filter', async function() {
        const totalAnalyses = 3
        const testState = createState(totalAnalyses)
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(sumAnalyses(state)).toEqual(totalAnalyses)
    })
})

function createState(numAnalyses) {
    const analyses = []
    do {
        analyses.push(createAnalysis())
        numAnalyses = numAnalyses ? numAnalyses - 1 : 0
    } while (numAnalyses > 0)
    return {
        views: {
            overview: {
                sectionKeys: [],
                sections: {},
                state: {
                    selectedSection: 'analyses'
                },
                filter: Object.assign({}, DEFAULT_FILTER),
                filteredAnalyses: [],
                data: {
                    analyses: {
                        marked_medicalreview: [],
                        marked_review_all_classified: [],
                        marked_review_missing_alleleassessments: [],
                        not_ready: [],
                        not_started_all_classified: [],
                        not_started_missing_alleleassessments: analyses,
                        ongoing_others: [],
                        ongoing_user: []
                    }
                }
            }
        }
    }
}

function createAnalysis(numSamples) {
    const samples = []
    do {
        samples.push(createSample())
        numSamples = numSamples ? numSamples - 1 : 0
    } while (numSamples > 0)
    return {
        date_deposited: `${new Date().toISOString()}`,
        date_requested: `${new Date().toISOString()}`,
        name: 'default_analysis.genepanel_version',
        priority: 1,
        samples: samples
    }
}

function createSample() {
    return {
        affected: true,
        identifier: 'default_analysis',
        proband: true,
        sample_type: 'HTS'
    }
}

function sumAnalyses(state) {
    const sectionTotals = []
    for (let [sectionName, sectionAnalyses] of Object.entries(
        state.views.overview.filteredAnalyses
    )) {
        sectionTotals.push(sectionAnalyses.length)
    }
    return sectionTotals.reduce((a, b) => a + b, 0)
}
