import { runAction } from 'cerebral/test'

import prepareInterpretationState from './prepareInterpretationState'

describe('prepareInterpretationState', function() {
    it('is initialized when state is empty', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {},
                            user_state: {}
                        }
                    },
                    data: {
                        alleles: {
                            1: {}
                        }
                    }
                }
            }
        }
        return runAction(prepareInterpretationState, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.selected.state.allele[1]).toBeDefined()
            expect(state.views.workflows.interpretation.selected.user_state.allele[1]).toBeDefined()
        })
    })

    it('has alleleasssessments and allelereports copied when not existing', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {},
                            user_state: {}
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                allele_assessment: {
                                    id: 1,
                                    evaluation: {},
                                    classification: '1'
                                },
                                allele_report: {
                                    id: 1,
                                    evaluation: {}
                                }
                            }
                        }
                    }
                }
            }
        }
        return runAction(prepareInterpretationState, { state: testState }).then(({ state }) => {
            expect(
                state.views.workflows.interpretation.selected.state.allele[1].alleleassessment
            ).toEqual(
                jasmine.objectContaining({
                    copiedFromId: 1,
                    classification: '1'
                })
            )
            expect(
                state.views.workflows.interpretation.selected.state.allele[1].allelereport
            ).toEqual(
                jasmine.objectContaining({
                    copiedFromId: 1
                })
            )
        })
    })

    it('has alleleasssessments and allelereports not copied again when already copied', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: {
                                        alleleassessment: {
                                            copiedFromId: 1,
                                            classification: '5'
                                        },
                                        allelereport: {
                                            copiedFromId: 1,
                                            evaluation: { comment: 'old comment' }
                                        }
                                    }
                                }
                            },
                            user_state: {}
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                allele_assessment: {
                                    id: 1,
                                    evaluation: {},
                                    classification: '1'
                                },
                                allele_report: {
                                    id: 1,
                                    evaluation: { comment: 'new comment' }
                                }
                            }
                        }
                    }
                }
            }
        }
        return runAction(prepareInterpretationState, { state: testState }).then(({ state }) => {
            expect(
                state.views.workflows.interpretation.selected.state.allele[1].alleleassessment
            ).toEqual(
                jasmine.objectContaining({
                    copiedFromId: 1,
                    classification: '5'
                })
            )
            expect(
                state.views.workflows.interpretation.selected.state.allele[1].allelereport
            ).toEqual(
                jasmine.objectContaining({
                    copiedFromId: 1,
                    evaluation: { comment: 'old comment' }
                })
            )
        })
    })

    it('has alleleasssessments and allelereports copied when newer', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: {
                                        alleleassessment: {
                                            copiedFromId: 1,
                                            classification: '5'
                                        },
                                        allelereport: {
                                            copiedFromId: 1,
                                            evaluation: { comment: 'old comment' }
                                        }
                                    }
                                }
                            },
                            user_state: {}
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                allele_assessment: {
                                    id: 500,
                                    evaluation: {},
                                    classification: '1'
                                },
                                allele_report: {
                                    id: 500,
                                    evaluation: { comment: 'new comment' }
                                }
                            }
                        }
                    }
                }
            }
        }
        return runAction(prepareInterpretationState, { state: testState }).then(({ state }) => {
            expect(
                state.views.workflows.interpretation.selected.state.allele[1].alleleassessment
            ).toEqual(
                jasmine.objectContaining({
                    copiedFromId: 500,
                    classification: '1'
                })
            )
            expect(
                state.views.workflows.interpretation.selected.state.allele[1].allelereport
            ).toEqual(
                jasmine.objectContaining({
                    copiedFromId: 500,
                    evaluation: { comment: 'new comment' }
                })
            )
        })
    })
})
