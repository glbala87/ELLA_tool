import { runAction } from 'cerebral/test'

import finishWorkflow from './finishWorkflow'

describe('finishWorkflow', function() {
    it('prepares payload correctly', function() {
        const testState = {
            views: {
                workflows: {
                    type: 'analysis',
                    id: 1,
                    interpretation: {
                        selected: {
                            genepanel_name: 'Test',
                            genepanel_version: 'v01',
                            status: 'Ongoing',
                            state: {
                                allele: {
                                    1: {
                                        allele_id: 1,
                                        alleleassessment: {
                                            id: 1,
                                            reuse: true
                                        },
                                        allelereport: {
                                            id: 1,
                                            reuse: true,
                                            evaluation: { comment: 'Same' }
                                        },
                                        referenceassessments: [
                                            {
                                                id: 1, // Backend uses id instead of reuse just to be inconsistent
                                                reuse: true, // reuse flag is still set by frontend..
                                                allele_id: 1,
                                                reference_id: 1
                                            },
                                            {
                                                allele_id: 1,
                                                reference_id: 2,
                                                reuse: false,
                                                evaluation: { comment: 'New' }
                                            }
                                        ]
                                    },
                                    2: {
                                        allele_id: 2,
                                        alleleassessment: {
                                            id: 2,
                                            reuse: false,
                                            classification: '5',
                                            evaluation: { test: 'comment' }
                                        },
                                        allelereport: {
                                            evaluation: { comment: 'Different' }
                                        },
                                        referenceassessments: [
                                            // We didn't evaluate reference id 1, so not present in state
                                            {
                                                allele_id: 2,
                                                reference_id: 2,
                                                reuse: false,
                                                evaluation: { comment: 'New' }
                                            }
                                        ]
                                    },
                                    3: {
                                        allele_id: 3,
                                        alleleassessment: {
                                            id: 3,
                                            classification: '4',
                                            evaluation: { test: 'another comment' }
                                        },
                                        allelereport: {
                                            evaluation: {}
                                        },
                                        referenceassessments: [
                                            {
                                                allele_id: 3,
                                                reference_id: 1,
                                                id: 3 // reusing
                                            },
                                            {
                                                // Reference id 2 is not present in references for this allele
                                                // -> should therefore not be included in payload
                                                allele_id: 3,
                                                reference_id: 2,
                                                evaluation: {
                                                    comment: "Reference id doesn't exist"
                                                }
                                            }
                                        ]
                                    }
                                }
                            },
                            user_state: {}
                        }
                    },
                    data: {
                        alleles: {
                            1: {
                                id: 1,
                                allele_assessment: {
                                    id: 1
                                },
                                allele_report: {
                                    id: 1,
                                    evaluation: { comment: 'Same' }
                                },
                                reference_assessments: {
                                    allele_id: 1,
                                    reference_id: 1,
                                    evaluation: { test: 'comment' }
                                },
                                annotation: {
                                    annotation_id: 1,
                                    custom_annotation_id: 1,
                                    references: [{ id: 1 }, { id: 2 }]
                                }
                            },
                            2: {
                                id: 2,
                                allele_assessment: {
                                    id: 2
                                },
                                allele_report: {
                                    id: 2,
                                    evaluation: { comment: 'Not same' }
                                },
                                reference_assessments: {
                                    id: 2,
                                    allele_id: 1,
                                    reference_id: 1,
                                    evaluation: { test: 'comment' }
                                },
                                annotation: {
                                    annotation_id: 2,
                                    custom_annotation_id: 2,
                                    references: [{ id: 1 }, { id: 2 }]
                                }
                            },
                            3: {
                                id: 3,
                                annotation: {
                                    annotation_id: 3,
                                    references: [{ id: 1 }]
                                }
                            }
                        },
                        references: {
                            1: {
                                id: 1
                            },
                            2: {
                                id: 2
                            }
                        }
                    }
                }
            }
        }
        const http = {
            post(url, payload) {
                // Annotation
                expect(payload.annotations).toEqual([
                    {
                        allele_id: 1,
                        annotation_id: 1
                    },
                    {
                        allele_id: 2,
                        annotation_id: 2
                    },
                    {
                        allele_id: 3,
                        annotation_id: 3
                    }
                ])

                // Custom annotation
                expect(payload.custom_annotations).toEqual([
                    {
                        allele_id: 1,
                        custom_annotation_id: 1
                    },
                    {
                        allele_id: 2,
                        custom_annotation_id: 2
                    }
                ])

                // Alleleassessments
                expect(payload.alleleassessments).toEqual([
                    {
                        allele_id: 1,
                        reuse: true,
                        presented_alleleassessment_id: 1,
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    },
                    {
                        allele_id: 2,
                        reuse: false,
                        presented_alleleassessment_id: 2,
                        evaluation: { test: 'comment' },
                        classification: '5',
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    },
                    {
                        allele_id: 3,
                        reuse: false,
                        evaluation: { test: 'another comment' },
                        classification: '4',
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    }
                ])

                // Allelereports
                expect(payload.allelereports).toEqual([
                    {
                        allele_id: 1,
                        reuse: true,
                        presented_allelereport_id: 1,
                        alleleassessment_id: 1,
                        analysis_id: 1
                    },
                    {
                        allele_id: 2,
                        reuse: false,
                        presented_allelereport_id: 2,
                        evaluation: { comment: 'Different' },
                        alleleassessment_id: 2,
                        analysis_id: 1
                    },
                    {
                        allele_id: 3,
                        reuse: false,
                        evaluation: {},
                        analysis_id: 1
                    }
                ])

                // Referenceassessments
                expect(payload.referenceassessments).toEqual([
                    {
                        allele_id: 1,
                        reference_id: 1,
                        id: 1,
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    },
                    {
                        allele_id: 1,
                        reference_id: 2,
                        evaluation: { comment: 'New' },
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    },
                    {
                        allele_id: 2,
                        reference_id: 2,
                        evaluation: { comment: 'New' },
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    },
                    {
                        allele_id: 3,
                        reference_id: 1,
                        id: 3,
                        genepanel_name: 'Test',
                        genepanel_version: 'v01',
                        analysis_id: 1
                    }
                ])

                return Promise.resolve({})
            }
        }
        const path = {
            success() {},
            error() {}
        }
        return runAction(finishWorkflow('Finalized'), {
            providers: { http, path },
            state: testState
        })
            .then(() => {})
            .catch((err) => {
                console.error(err.message, err.stack)
                expect(1).toBe(0)
            })
    })
})
