import { runAction } from 'cerebral/test'

import autoReuseExistingAlleleassessments from './autoReuseExistingAlleleassessments'

describe('autoReuseExistingAlleleassessments', function() {
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
                        state: { allele: { 1: { alleleassessment: {} } } },
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
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuseCheckedId: 2,
                    reuse: true
                })
                expect(output.checkReportAlleleIds).toEqual([1])
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
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuseCheckedId: 2,
                    reuse: false
                })
                expect(output.checkReportAlleleIds).toEqual([])
            }
        )
    })

    it('is set to reuse true if outdated while previously reused', function() {
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
                        state: {
                            allele: {
                                1: { alleleassessment: { reuseCheckedId: 2, reuse: true } }
                            }
                        }, // Was previously valid and reused
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
        }

        return runAction(autoReuseExistingAlleleassessments, { state: testState }).then(
            ({ state, output }) => {
                expect(
                    state.views.workflows.interpretation.state.allele['1'].alleleassessment
                ).toEqual({
                    allele_id: 1,
                    reuse: true,
                    reuseCheckedId: 2
                })
                expect(output.checkReportAlleleIds).toEqual([1])
            }
        )
    })
})
