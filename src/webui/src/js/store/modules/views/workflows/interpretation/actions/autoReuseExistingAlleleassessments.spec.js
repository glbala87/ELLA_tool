import { runAction } from 'cerebral/test'

import autoReuseExistingAlleleassessments from './autoReuseExistingAlleleassessments'

describe('autoReuseExistingAlleleassessments', function() {
    it('disables reuse if outdated assessment', function() {
        const testState = {
            app: {
                config: {
                    classification: {
                        options: [
                            {
                                value: '5',
                                outdated_after_days: 3
                            }
                        ]
                    }
                }
            },
            views: {
                workflows: {
                    interpretation: {
                        selected: { state: { allele: { 1: { alleleassessment: {} } } } }
                    },
                    data: {
                        alleles: {
                            1: {
                                id: 1,
                                allele_assessment: {
                                    id: 1,
                                    seconds_since_update: 4 * 24 * 3600,
                                    classification: '5'
                                }
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuseCheckedId: 1,
                    reuse: false
                })
                expect(output.checkReportAlleleIds).toEqual([1])
                expect(output.copyExistingAlleleAssessmentAlleleIds).toEqual([1])
            }
        )
    })

    it('is checked if not checked previously', function() {
        const testState = {
            app: {
                config: {
                    classification: {
                        options: [
                            {
                                value: '5',
                                outdated_after_days: 3
                            }
                        ]
                    }
                }
            },
            views: {
                workflows: {
                    interpretation: {
                        selected: { state: { allele: { 1: { alleleassessment: {} } } } }
                    },
                    data: {
                        alleles: {
                            1: {
                                id: 1,
                                allele_assessment: {
                                    id: 2,
                                    seconds_since_update: 1 * 24 * 3600,
                                    classification: '5'
                                }
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuseCheckedId: 2,
                    reuse: true
                })
                expect(output.checkReportAlleleIds).toEqual([1])
                expect(output.copyExistingAlleleAssessmentAlleleIds).toEqual([])
            }
        )
    })

    it('is not checked if checked previously', function() {
        const testState = {
            app: {
                config: {
                    classification: {
                        options: [
                            {
                                value: '5',
                                outdated_after_days: 3
                            }
                        ]
                    }
                }
            },
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: {
                                        alleleassessment: {
                                            reuseCheckedId: 2,
                                            reuse: false,
                                            allele_id: 1
                                        }
                                    }
                                }
                            }
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                allele_assessment: {
                                    id: 2,
                                    seconds_since_update: 1 * 24 * 3600,
                                    classification: '5'
                                }
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuseCheckedId: 2,
                    reuse: false
                })
                expect(output.checkReportAlleleIds).toEqual([])
                expect(output.copyExistingAlleleAssessmentAlleleIds).toEqual([])
            }
        )
    })

    it('is set to reuse false if outdated while previously reused', function() {
        const testState = {
            app: {
                config: {
                    classification: {
                        options: [
                            {
                                value: '5',
                                outdated_after_days: 3
                            }
                        ]
                    }
                }
            },
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: { alleleassessment: { reuseCheckedId: 2, reuse: true } }
                                }
                            } // Was previously valid and reused
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                id: 1,
                                allele_assessment: {
                                    id: 2,
                                    seconds_since_update: 4 * 24 * 3600, // Outdated
                                    classification: '5',
                                    evaluation: {
                                        key: 'WAS VALID REUSED, NOW OUTDATED'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuse: false,
                    reuseCheckedId: 2
                })
                expect(output.checkReportAlleleIds).toEqual([1])
                expect(output.copyExistingAlleleAssessmentAlleleIds).toEqual([1])
            }
        )
    })
})