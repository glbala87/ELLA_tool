import { runAction } from 'cerebral/test'

import setManuallyAddedAlleleIds from './setManuallyAddedAlleleIds'

function createState(snvFiltered, filteredAlleleIds) {
    return {
        views: {
            workflows: {
                alleleSidebar: {
                    callerTypeSelected: 'snv'
                },
                interpretation: {
                    state: {
                        manuallyAddedAlleles: {
                            cnv: [],
                            snv: snvFiltered
                        }
                    },
                    data: {
                        filteredAlleleIds
                    }
                }
            }
        }
    }
}

describe('setManuallyAddedAlleleIds', function() {
    it('adds included to empty existing', async function() {
        const testState = createState([], {
            allele_ids: [],
            excluded_allele_ids: { test: [1, 2, 3] }
        })
        const props = {
            includedAlleleIds: [1, 2, 3]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3
        ])
    })

    it("doesn't duplicate existing", async function() {
        const testState = createState([1, 2, 3], {
            allele_ids: [],
            excluded_allele_ids: { test: [1, 2, 3] }
        })
        const props = {
            includedAlleleIds: [1, 2, 3]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3
        ])
    })

    it("doesn't remove existing", async function() {
        const testState = createState([1, 2, 3], {
            allele_ids: [1, 2],
            excluded_allele_ids: { test: [3, 4, 5] }
        })
        const props = {
            includedAlleleIds: [3, 4, 5]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3,
            4,
            5
        ])
    })

    it("doesn't remove existing when empty list", async function() {
        const testState = createState([1, 2, 3], {
            allele_ids: [1, 2, 3],
            excluded_allele_ids: { test: [] }
        })
        const props = {
            includedAlleleIds: []
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3
        ])
    })

    it('removes ids that were removed', async function() {
        const testState = createState([1, 2, 3], {
            allele_ids: [],
            excluded_allele_ids: { test: [1, 2, 3] }
        })
        const props = {
            includedAlleleIds: [1, 2]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([1, 2])
    })
})
