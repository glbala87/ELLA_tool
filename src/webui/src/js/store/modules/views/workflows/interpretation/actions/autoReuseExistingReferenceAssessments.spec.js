import { runAction } from 'cerebral/test'

import autoReuseExistingReferenceAssessments from './autoReuseExistingReferenceAssessments'

describe('autoReuseExistingReferenceAssessments', function() {
    it('is reused if not present already', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: { 1: { alleleassessment: {}, referenceassessments: [] } }
                            }
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                reference_assessments: [
                                    {
                                        id: 10,
                                        reference_id: 1,
                                        allele_id: 1
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingReferenceAssessments, { state: testState }).then(
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele[1]
                        .referenceassessments
                ).toEqual([
                    {
                        id: 10,
                        reference_id: 1,
                        allele_id: 1,
                        reuseCheckedId: 10,
                        reuse: true
                    }
                ])
            }
        )
    })

    it('is reused if already present is older', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: {
                                        alleleassessment: {},
                                        referenceassessments: [
                                            {
                                                id: 10,
                                                reference_id: 1,
                                                allele_id: 1,
                                                reuseCheckedId: 10,
                                                reuse: false
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                reference_assessments: [
                                    {
                                        id: 20,
                                        reference_id: 1,
                                        allele_id: 1
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingReferenceAssessments, { state: testState }).then(
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele[1]
                        .referenceassessments
                ).toEqual([
                    {
                        id: 20,
                        reference_id: 1,
                        allele_id: 1,
                        reuseCheckedId: 20,
                        reuse: true
                    }
                ])
            }
        )
    })

    it('is not reused if already present is same', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: {
                                        alleleassessment: {},
                                        referenceassessments: [
                                            {
                                                id: 10,
                                                reference_id: 1,
                                                allele_id: 1,
                                                reuseCheckedId: 10,
                                                reuse: false
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                reference_assessments: [
                                    {
                                        id: 10,
                                        reference_id: 1,
                                        allele_id: 1
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingReferenceAssessments, { state: testState }).then(
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele[1]
                        .referenceassessments
                ).toEqual([
                    {
                        id: 10,
                        reference_id: 1,
                        allele_id: 1,
                        reuseCheckedId: 10,
                        reuse: false
                    }
                ])
            }
        )
    })

    it('is empty when alleleassessment is reused', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        selected: {
                            state: {
                                allele: {
                                    1: {
                                        alleleassessment: { reuse: true },
                                        referenceassessments: [
                                            {
                                                id: 10,
                                                reference_id: 1,
                                                allele_id: 1,
                                                reuseCheckedId: 10,
                                                reuse: false
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                reference_assessments: [
                                    {
                                        id: 10,
                                        reference_id: 1,
                                        allele_id: 1
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoReuseExistingReferenceAssessments, { state: testState }).then(
            ({ state }) => {
                expect(
                    state.views.workflows.interpretation.selected.state.allele[1]
                        .referenceassessments
                ).toEqual([])
            }
        )
    })
})
