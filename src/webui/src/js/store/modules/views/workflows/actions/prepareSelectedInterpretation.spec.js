import { runAction, runCompute } from 'cerebral/test'

import selectDefaultInterpretation from './selectDefaultInterpretation'
import getSelectedInterpretation from '../computed/getSelectedInterpretation'
import copyInterpretationState from './copyInterpretationState'

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
                        alleles: null
                    }
                }
            }
        }

        return runAction(selectDefaultInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation).toEqual({
                selectedId: 'current'
            })
            const interpretation = runCompute(getSelectedInterpretation, { state })
            expect(interpretation).toEqual({
                state: {},
                user_state: {},
                status: 'Not started'
            })

            return runAction(copyInterpretationState, { state }).then(({ state }) => {
                expect(state.views.workflows.interpretation).toEqual({
                    selectedId: 'current',
                    state: {},
                    userState: {},
                    isOngoing: false
                })
            })
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
                                status: 'Done',
                                state: {
                                    STATE1: null
                                },
                                user_state: {
                                    USERSTATE1: null
                                }
                            },
                            {
                                id: 2,
                                status: 'Ongoing',
                                state: {
                                    STATE2: null
                                },
                                user_state: {
                                    USERSTATE2: null
                                }
                            }
                        ]
                    }
                }
            }
        }

        return runAction(selectDefaultInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selectedId).toEqual(2)
            const interpretation = runCompute(getSelectedInterpretation, { state })
            expect(interpretation).toEqual(testState.views.workflows.data.interpretations[1])
            return runAction(copyInterpretationState, { state }).then(({ state }) => {
                expect(state.views.workflows.interpretation).toEqual({
                    selectedId: 2,
                    state: {
                        STATE2: null
                    },
                    userState: {
                        USERSTATE2: null
                    },
                    isOngoing: true
                })
            })
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
                                status: 'Done',
                                state: {
                                    STATE1: null
                                },
                                user_state: {
                                    USERSTATE1: null
                                }
                            },
                            {
                                id: 2,
                                status: 'Done',
                                state: {
                                    STATE2: null
                                },
                                user_state: {
                                    USERSTATE2: null
                                }
                            }
                        ]
                    }
                }
            }
        }

        return runAction(selectDefaultInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selectedId).toEqual('current')
            const interpretation = runCompute(getSelectedInterpretation, { state })
            expect(interpretation).toEqual(testState.views.workflows.data.interpretations[1])
            return runAction(copyInterpretationState, { state }).then(({ state }) => {
                expect(state.views.workflows.interpretation).toEqual({
                    selectedId: 'current',
                    state: {
                        STATE2: null
                    },
                    userState: {
                        USERSTATE2: null
                    },
                    isOngoing: false
                })
            })
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
                                status: 'Not started',
                                state: {},
                                user_state: {}
                            }
                        ]
                    }
                }
            }
        }

        return runAction(selectDefaultInterpretation, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selectedId).toEqual(1)
            const interpretation = runCompute(getSelectedInterpretation, { state })
            expect(interpretation).toEqual(testState.views.workflows.data.interpretations[0])

            return runAction(copyInterpretationState, { state }).then(({ state }) => {
                expect(state.views.workflows.interpretation).toEqual({
                    selectedId: 1,
                    state: {},
                    userState: {},
                    isOngoing: false
                })
            })
        })
    })
})
