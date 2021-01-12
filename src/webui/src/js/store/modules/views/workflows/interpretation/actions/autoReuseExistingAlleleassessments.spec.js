import { runAction } from 'cerebral/test'

import autoReuseExistingAlleleassessments from './autoReuseExistingAlleleassessments'
import { prepareAlleleAssessmentModel } from '../../../../../common/helpers/alleleState'

const emptyAlleleAssessment = {}
prepareAlleleAssessmentModel(emptyAlleleAssessment)

describe('autoReuseExistingAlleleassessments', function() {
    it('is checked, but not updated, if assessment state is inital', function() {
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
                        state: { allele: { 1: { alleleassessment: emptyAlleleAssessment } } },
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
                expect(output.updatedAlleleAssessmentAlleleIds).toEqual([])
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
                expect(output.updatedAlleleAssessmentAlleleIds).toEqual([])
            }
        )
    })

    it('is checked if updated', function() {
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
                                    id: 1,
                                    allele_assessment: {
                                        id: 3,
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
                    reuseCheckedId: 3,
                    reuse: true
                })
                expect(output.checkReportAlleleIds).toEqual([1])
                expect(output.updatedAlleleAssessmentAlleleIds).toEqual([1])
            }
        )
    })

    it('is checked if new and updated, if state is not clean', function() {
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
                                        evaluation: {
                                            comment: 'dabla'
                                        },
                                        classification: '3'
                                    }
                                }
                            }
                        },
                        data: {
                            alleles: {
                                1: {
                                    id: 1,
                                    allele_assessment: {
                                        id: 3,
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
                    reuseCheckedId: 3,
                    reuse: true
                })
                expect(output.checkReportAlleleIds).toEqual([1])
                expect(output.updatedAlleleAssessmentAlleleIds).toEqual([1])
            }
        )
    })
})
