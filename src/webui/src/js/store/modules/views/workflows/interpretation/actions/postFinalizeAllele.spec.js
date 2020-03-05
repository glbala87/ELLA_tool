import mock from 'xhr-mock'
import { http } from '../../../../index'
import { runAction } from 'cerebral/test'

import postFinalizeAllele from './postFinalizeAllele'

function createState(state, alleles) {
    return {
        views: {
            workflows: {
                type: 'analysis',
                id: 1,
                selectedGenepanel: {
                    name: 'test',
                    version: 'v01'
                },
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
                    state,
                    userState: {},
                    data: {
                        alleles,
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
    }
}

describe('postFinalizeAllele', function() {
    beforeEach(() => mock.setup())
    afterEach(() => mock.teardown())

    it('correct payload when new alleleassessment', async function() {
        expect.assertions(1)

        const state = {
            allele: {
                1: {
                    allele_id: 1,
                    alleleassessment: {
                        classification: '1',
                        evaluation: { comment: 'new' },
                        attachment_ids: [1]
                    },
                    allelereport: {
                        evaluation: { comment: 'new' }
                    },
                    referenceassessments: [
                        {
                            allele_id: 1,
                            reference_id: 1,
                            evaluation: { comment: 'new' }
                        }
                    ],
                    analysis: {
                        comment: '',
                        verification: null,
                        notrelevant: null
                    }
                }
            }
        }

        const alleles = {
            1: {
                id: 1,
                annotation: {
                    annotation_id: 1,
                    custom_annotation_id: 1,
                    references: [{ id: 1 }, { id: 2 }]
                }
            }
        }

        const testState = createState(state, alleles)

        mock.error((err) => {
            throw err
        })

        mock.post('/api/v1/workflows/analyses/1/actions/finalizeallele/', (req, res) => {
            const response = res
                .status(200)
                .header('Content-Type', 'application/json')
                .body(
                    JSON.stringify({
                        alleleassessment: {
                            id: 1
                        },
                        allelereport: {
                            id: 1
                        }
                    })
                )
            const body = JSON.parse(req.body())
            expect(body).toEqual({
                allele_id: 1,
                alleleassessment: {
                    allele_id: 1,
                    attachment_ids: [1],
                    classification: '1',
                    evaluation: { comment: 'new' },
                    reuse: false
                },
                allelereport: {
                    allele_id: 1,
                    evaluation: { comment: 'new' },
                    reuse: false
                },
                annotation_id: 1,
                custom_annotation_id: 1,
                referenceassessments: [
                    {
                        allele_id: 1,
                        evaluation: { comment: 'new' },
                        reference_id: 1
                    }
                ]
            })
            return response
        })

        const path = {
            success() {},
            error() {}
        }
        await runAction(postFinalizeAllele, {
            props: { alleleId: 1 },
            providers: { http, path },
            state: testState
        })
    })

    it('correct payload when reusing existing', async function() {
        expect.assertions(1)

        const state = {
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
                        }
                    ],
                    analysis: {
                        comment: '',
                        verification: null,
                        notrelevant: null
                    }
                }
            }
        }

        const alleles = {
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
            }
        }

        const testState = createState(state, alleles)

        mock.error((err) => {
            throw err
        })

        mock.post('/api/v1/workflows/analyses/1/actions/finalizeallele/', (req, res) => {
            const response = res
                .status(200)
                .header('Content-Type', 'application/json')
                .body(
                    JSON.stringify({
                        result: {
                            alleleassessment: {
                                id: 1
                            },
                            allelereport: {
                                id: 1
                            }
                        }
                    })
                )
            const body = JSON.parse(req.body())
            expect(body).toEqual({
                allele_id: 1,
                annotation_id: 1,
                custom_annotation_id: 1,
                alleleassessment: {
                    allele_id: 1,
                    reuse: true,
                    presented_alleleassessment_id: 1
                },
                allelereport: {
                    allele_id: 1,
                    presented_allelereport_id: 1,
                    reuse: true
                },
                referenceassessments: [
                    {
                        reference_id: 1,
                        allele_id: 1,
                        id: 1
                    }
                ]
            })
            return response
        })
        const path = {
            success() {},
            error() {}
        }
        await runAction(postFinalizeAllele, {
            props: { alleleId: 1 },
            providers: { http, path },
            state: testState
        })
    })
})
