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
                        manuallyAddedAlleles: {
                            cnv: cnvFiltered,
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
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3
        ])
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.cnv).toEqual([])
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
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([])
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.cnv).toEqual([4, 5])
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
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3
        ])
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.cnv).toEqual([7, 8])
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
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3,
            4,
            5
        ])
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.cnv).toEqual([])
    })

    it("doesn't remove existing when empty list", async function() {
        const testState = createState(
            [1, 2, 3],
            [4, 5, 6],
            {
                allele_ids: [1, 2, 3],
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
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([
            1,
            2,
            3
        ])
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.cnv).toEqual([
            4,
            5,
            6
        ])
    })

    it('removes ids that were removed', async function() {
        const testState = createState(
            [1, 2, 3],
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
            includedAlleleIds: [1, 2]
        }
        const { state } = await runAction(setManuallyAddedAlleleIds, {
            state: testState,
            props
        })
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.snv).toEqual([1, 2])
        expect(state.views.workflows.interpretation.state.manuallyAddedAlleles.cnv).toEqual([])
    })
})
