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
                                allele_assessment: {
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
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                        .reuse
                ).toEqual(false)
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
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                        .reuse
                ).toEqual(true)
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                        .reuseCheckedId
                ).toEqual(2)
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
                            state: { allele: { 1: { alleleassessment: { reuseCheckedId: 2 } } } }
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
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele['1'].alleleassessment
                        .reuse
                ).toEqual(undefined)
            }
        )
    })
})
