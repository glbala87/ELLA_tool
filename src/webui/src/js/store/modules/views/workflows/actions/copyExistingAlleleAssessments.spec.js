import { runAction } from 'cerebral/test'

import copyExistingAlleleAssessments from './copyExistingAlleleAssessments'

describe('copyExistingAlleleAssessments', function() {
    it('has alleleasssessments copied when not existing, only specified ones', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: {}
                                },
                                2: {
                                    alleleassessment: {
                                        classification: 'dontReplaceMe'
                                    }
                                }
                            }
                        },
                        data: {
                            alleles: {
                                1: {
                                    allele_assessment: {
                                        evaluation: { someKey: 'someValue' },
                                        classification: '1',
                                        attachment_ids: [1]
                                    }
                                },
                                2: {
                                    allele_assessment: {
                                        evaluation: { someKey: 'someValue' },
                                        classification: 'replaceCandidiate',
                                        attachment_ids: [1]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return runAction(copyExistingAlleleAssessments, {
            state: testState,
            props: { copyExistingAlleleAssessmentAlleleIds: [1] }
        }).then(({ state }) => {
            const alleleAsssessment1 =
                state.views.workflows.interpretation.state.allele[1].alleleassessment
            expect(alleleAsssessment1).toEqual(
                jasmine.objectContaining({
                    classification: '1',
                    attachment_ids: [1]
                })
            )
            const alleleAsssessment2 =
                state.views.workflows.interpretation.state.allele[2].alleleassessment

            expect(alleleAsssessment2.evaluation).toEqual(undefined)
            expect(alleleAsssessment2.classification).toEqual('dontReplaceMe')
        })
    })
})
