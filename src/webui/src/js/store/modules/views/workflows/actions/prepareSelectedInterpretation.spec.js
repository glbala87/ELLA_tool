import { runAction } from 'cerebral/test'

import prepareSelectedInterpretation from './prepareSelectedInterpretation'

describe('prepareSelectedInterpretation', function() {
    it("creates dummy interpretation as selected when no alleles and type = 'allele'", function() {
        const testState = {
            views: {
                workflows: {
                    type: 'allele',
                    allele: {
                        id: 1
                    },
                    data: {
                        interpretations: [],
                        alleles: null,
                        genepanel: {
                            name: 'Test',
                            version: 'v01'
                        }
                    }
                }
            }
        }

        return runAction(prepareSelectedInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selected).toEqual({
                genepanel_name: 'Test',
                genepanel_version: 'v01',
                state: {},
                user_state: {},
                status: 'Not started',
                allele_ids: [1]
            })
            expect(state.views.workflows.historyInterpretations).toEqual([])
            expect(state.views.workflows.interpretation.isOngoing).toEqual(false)
        })
    })

    it("assings ongoing interpretations directly'", function() {
        const testState = {
            views: {
                workflows: {
                    data: {
                        interpretations: [
                            {
                                id: 1,
                                status: 'Done'
                            },
                            {
                                id: 2,
                                status: 'Ongoing'
                            }
                        ]
                    }
                }
            }
        }

        return runAction(prepareSelectedInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selected).toEqual(
                testState.views.workflows.data.interpretations[1]
            )
            expect(state.views.workflows.historyInterpretations).toEqual([
                testState.views.workflows.data.interpretations[0]
            ])
            expect(state.views.workflows.interpretation.isOngoing).toEqual(true)
        })
    })

    it("creates a 'Current' copy when no Ongoing, but history is present", function() {
        const testState = {
            views: {
                workflows: {
                    data: {
                        interpretations: [
                            {
                                id: 1,
                                status: 'Done'
                            },
                            {
                                id: 2,
                                status: 'Done'
                            }
                        ]
                    }
                }
            }
        }

        return runAction(prepareSelectedInterpretation, { state: testState }).then(({ state }) => {
            const currentInterpretationCopy = Object.assign(
                {},
                testState.views.workflows.data.interpretations[1],
                { current: true }
            )
            expect(state.views.workflows.interpretation.selected).toEqual(currentInterpretationCopy)
            expect(state.views.workflows.historyInterpretations).toEqual(
                testState.views.workflows.data.interpretations.concat(currentInterpretationCopy)
            )
            expect(state.views.workflows.interpretation.isOngoing).toEqual(false)
        })
    })

    it('assigns the only interpretation when when no history is present', function() {
        const testState = {
            views: {
                workflows: {
                    data: {
                        interpretations: [
                            {
                                id: 1,
                                status: 'Not started'
                            }
                        ]
                    }
                }
            }
        }

        return runAction(prepareSelectedInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selected).toEqual(
                testState.views.workflows.data.interpretations[0]
            )
            expect(state.views.workflows.historyInterpretations).toEqual([])
            expect(state.views.workflows.interpretation.isOngoing).toEqual(false)
        })
    })
})
