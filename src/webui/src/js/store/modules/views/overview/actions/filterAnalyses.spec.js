import { runAction } from 'cerebral/test'

import filterAnalyses from './filterAnalyses'
import { DEFAULT_FILTER } from '../getOverviewState'

describe('filterAnalyses', function() {
    it('default filter', async function() {
        const filter = Object.assign({}, DEFAULT_FILTER)
        const testState = createState([{ name: 'test' }], filter)
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(getAnalysesNames(state)).toEqual(['test'])
    })

    it('name filter', async function() {
        const testState = createState(
            [{ name: 'Matching name' }, { name: 'Something else' }],
            Object.assign({}, DEFAULT_FILTER, {
                analysisName: 'match'
            })
        )
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(getAnalysesNames(state)).toEqual(['Matching name'])
    })

    it('comment filter', async function() {
        const testState = createState(
            [
                { name: 'No comment', review_comment: null },
                { name: 'With matching comment', review_comment: 'PATTERN' },
                { name: 'With non-matching comment', review_comment: 'Something else' }
            ],
            Object.assign({}, DEFAULT_FILTER, {
                reviewComment: 'PAT'
            })
        )
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(getAnalysesNames(state)).toEqual(['With matching comment'])
    })

    it('date range filter', async function() {
        const testState = createState(
            [
                { name: 'New', date_requested: new Date() },
                {
                    name: 'Old only deposited',
                    date_requested: null,
                    date_deposited: new Date('2020-01-01')
                },
                { name: 'Old', date_requested: new Date('2020-01-01') }
            ],
            Object.assign({}, DEFAULT_FILTER, {
                // Relies on when test is run, but should be valid unless going back in time
                dateRange: 'ge:-3:m'
            })
        )
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(getAnalysesNames(state)).toEqual(['Old only deposited', 'Old'])
    })

    it('priority filter', async function() {
        const testState = createState(
            [
                { name: 'P1', priority: 1 },
                { name: 'P2', priority: 2 },
                { name: 'P3', priority: 3 }
            ],
            Object.assign({}, DEFAULT_FILTER, {
                priorityNormal: false,
                priorityHigh: true,
                priorityUrgent: true
            })
        )
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(getAnalysesNames(state)).toEqual(['P2', 'P3'])
    })

    it('technology filter', async function() {
        const testState = createState(
            [
                { name: 'HTS', samples: ['HTS'] },
                { name: 'Sanger', samples: ['Sanger'] },
                { name: 'Both', samples: ['HTS', 'Sanger'] }
            ],
            Object.assign({}, DEFAULT_FILTER, {
                technologyHTS: false,
                technologySanger: true
            })
        )
        const { state } = await runAction(filterAnalyses, { state: testState })
        expect(getAnalysesNames(state)).toEqual(['Sanger', 'Both'])
    })
})

function createState(analysesProps, filter) {
    const analyses = []
    for (let analysisProps of analysesProps) {
        analyses.push(createAnalysis(analysisProps))
    }
    return {
        views: {
            overview: {
                sectionKeys: [],
                sections: {},
                state: {
                    selectedSection: 'analyses'
                },
                filter: filter,
                filteredAnalyses: [],
                data: {
                    analyses: {
                        marked_medicalreview: [],
                        marked_review: [],
                        not_ready: [],
                        not_started: analyses,
                        ongoing_others: [],
                        ongoing_user: []
                    }
                }
            }
        }
    }
}

function createAnalysis(analysisProps) {
    // {
    //     name: String,
    //     date_requested: String,
    //     date_deposited: String,
    //     priority: Number,
    //     review_comment: String,
    //     samples: Array[String] // technologies
    // }
    const DEFAULT = {
        name: 'Default name',
        date_requested: new Date(),
        date_deposited: new Date(),
        priority: 1,
        review_comment: null,
        samples: ['HTS']
    }
    analysisProps = Object.assign({}, DEFAULT, analysisProps)
    const analysis = {}
    analysis.date_deposited = analysisProps.date_deposited
        ? analysisProps.date_deposited.toISOString()
        : null
    analysis.date_requested = analysisProps.date_requested
        ? analysisProps.date_requested.toISOString()
        : null
    analysis.name = analysisProps.name
    analysis.priority = analysisProps.priority || 1
    analysis.review_comment = analysisProps.review_comment
    analysis.samples = analysisProps.samples.map((t) => {
        return {
            affected: true,
            identifier: analysisProps.name + ' sample',
            proband: true,
            sample_type: t
        }
    })
    return analysis
}

function getAnalysesNames(state) {
    const names = []
    for (let [sectionName, sectionAnalyses] of Object.entries(
        state.views.overview.filteredAnalyses
    )) {
        names.push(...sectionAnalyses.map((a) => a.name))
    }
    return names
}
