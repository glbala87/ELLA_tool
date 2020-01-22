import { runAction } from 'cerebral/test'

import finishWorkflow from './finishWorkflow'

describe('finishWorkflow', function() {
    it('prepares payload correctly', async function() {
        expect.assertions(1)

        const testState = {
            views: {
                workflows: {
                    type: 'analysis',
                    id: 1,
                    data: {
                        interpretations: [
                            {
                                id: 1,
                                status: 'Ongoing',
                                state: {},
                                user_state: {},
                                genepanel_name: 'Test',
                                genepanel_version: 'v01'
                            }
                        ]
                    },
                    interpretation: {
                        selectedId: 1,
                        state: {
                            manuallyAddedAlleles: [3],
                            allele: {
                                1: {
                                    allele_id: 1,
                                    alleleassessment: {
                                        id: 1,
                                        reuse: true
                                    },
                                    allelereport: {
                                        id: 1,
                                        reuse: true
                                    },
                                    analysis: {
                                        verification: null,
                                        notrelevant: null
                                    }
                                },
                                2: {
                                    allele_id: 2,
                                    alleleassessment: {},
                                    allelereport: {},
                                    analysis: {
                                        verification: 'technical',
                                        notrelevant: null
                                    }
                                },
                                3: {
                                    allele_id: 3,
                                    alleleassessment: {},
                                    allelereport: {},
                                    analysis: {
                                        verification: null,
                                        notrelevant: true
                                    }
                                }
                            }
                        },
                        userState: {},
                        data: {
                            filteredAlleleIds: {
                                allele_ids: [1, 2],
                                excluded_allele_ids: {
                                    testFilter: [3]
                                }
                            },
                            alleles: {
                                1: {
                                    id: 1,
                                    allele_assessment: {
                                        id: 1
                                    },
                                    allele_report: {
                                        id: 1
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
                                        id: 2
                                    },
                                    annotation: {
                                        annotation_id: 2,
                                        custom_annotation_id: 2
                                    }
                                },
                                3: {
                                    id: 3,
                                    annotation: {
                                        annotation_id: 3
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        const http = {
            post(url, payload) {
                expect(payload).toEqual({
                    annotation_ids: [1, 2, 3],
                    custom_annotation_ids: [1, 2],
                    alleleassessment_ids: [1, 2],
                    allelereport_ids: [1, 2],
                    allele_ids: [1, 2, 3],
                    technical_allele_ids: [2],
                    notrelevant_allele_ids: [3],
                    excluded_allele_ids: {
                        testFilter: [3]
                    }
                })

                return Promise.resolve({})
            }
        }
        const path = {
            success() {},
            error() {}
        }
        await runAction(finishWorkflow('Finalized'), {
            providers: { http, path },
            state: testState
        })
    })
})
