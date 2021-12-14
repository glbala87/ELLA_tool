import { runAction } from 'cerebral/test'

import setManuallyAddedAlleleIds from './setManuallyAddedAlleleIds'

function createState(snvFiltered, cnvFiltered, filteredAlleleIds, callerType) {
    return {
        views: {
            workflows: {
                alleleSidebar: {
                    callerTypeSelected: callerType
                },
                interpretation: {
                    state: {
                        manuallyAddedAlleles: [...cnvFiltered, ...snvFiltered]
                    },
                    data: {
                        filteredAlleleIds,
                        alleles: {
                            1: { caller_type: 'snv', id: 1 },
                            2: { caller_type: 'snv', id: 2 },
                            3: { caller_type: 'snv', id: 3 },
                            4: { caller_type: 'cnv', id: 4 },
                            5: { caller_type: 'cnv', id: 5 },
                            6: { caller_type: 'cnv', id: 6 },
                            7: { caller_type: 'cnv', id: 7 },
                            8: { caller_type: 'cnv', id: 8 }
                        }
                    }
                }
            }
        }
    }
}

describe('setManuallyAddedAlleleIds', function() {
    it('adds included to empty existing for snv', async function() {
        const testState = createState(
            [],
            [],
            {
                allele_ids: [],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: [1, 2, 3]
                    },
                    cnv: {
                        test: [4, 5, 6]
                    }
                }
            },
            'snv'
        )
        const props = {
            includedAlleleIds: [1, 2, 3]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles).toEqual([1, 2, 3])
    })

    it('adds included to empty existing for cnv', async function() {
        const testState = createState(
            [],
            [],
            {
                allele_ids: [],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: [1, 2, 3]
                    },
                    cnv: {
                        test: [4, 5, 6]
                    }
                }
            },
            'cnv'
        )
        const props = {
            includedAlleleIds: [4, 5]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles).toEqual([4, 5])
    })

    it("doesn't duplicate existing snv", async function() {
        const testState = createState(
            [1, 2, 3],
            [7, 8],
            {
                allele_ids: [],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: [1, 2, 3]
                    },
                    cnv: {
                        test: [4, 5, 6, 7, 8]
                    }
                }
            },
            'snv'
        )
        const props = {
            includedAlleleIds: [1, 2, 3]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, { state: testState, props })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.sort()).toEqual(
            [1, 2, 3, 7, 8].sort()
        )
    })

    it("doesn't remove existing snv", async function() {
        const testState = createState(
            [1, 2, 3],
            [],
            {
                allele_ids: [1, 2],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: [3, 4, 5]
                    }
                }
            },
            'snv'
        )
        const props = {
            includedAlleleIds: [3, 4, 5]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, {
            state: testState,
            props
        })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles).toEqual([
            1,
            2,
            3,
            4,
            5
        ])
    })

    it("doesn't remove existing when empty list", async function() {
        const testState = createState(
            [1, 2, 3],
            [4, 5, 6],
            {
                allele_ids: [1, 2, 3, 4, 5, 6],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: []
                    },
                    cnv: {
                        test: []
                    }
                }
            },
            'snv'
        )
        const props = {
            includedAlleleIds: []
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, {
            state: testState,
            props
        })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.sort()).toEqual(
            [1, 2, 3, 4, 5, 6].sort()
        )
    })

    it('removes snv ids that were removed', async function() {
        const testState = createState(
            [1, 2, 3],
            [4, 5],
            {
                allele_ids: [],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: [1, 2, 3]
                    },
                    cnv: {
                        test: [4, 5, 6]
                    }
                }
            },
            'snv'
        )
        const props = {
            includedAlleleIds: [1, 2]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, {
            state: testState,
            props
        })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.sort()).toEqual(
            [1, 2, 4, 5].sort()
        )
    })

    it('removes cnv ids that were removed', async function() {
        const testState = createState(
            [1, 2, 3],
            [4, 5, 6],
            {
                allele_ids: [],
                excluded_alleles_by_caller_type: {
                    snv: {
                        test: [1, 2, 3]
                    },
                    cnv: {
                        test: [4, 5, 6]
                    }
                }
            },
            'cnv'
        )
        const props = {
            includedAlleleIds: [4]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, {
            state: testState,
            props
        })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.sort()).toEqual(
            [1, 2, 3, 4].sort()
        )
    })
})
