import page from 'page'
import { Module } from 'cerebral'
import { CerebralTest } from 'cerebral/test'
import mock from 'xhr-mock'
import RootModule from '../..'
import setReferenceAssessment from './interpretation/actions/setReferenceAssessment'
import reuseAlleleAssessmentClicked from './interpretation/signals/reuseAlleleAssessmentClicked'
import prepareInterpretationState from './sequences/prepareInterpretationState'
import finishConfirmationClicked from './modals/finishConfirmation/signals/finishConfirmationClicked'
import copyInterpretationState from './actions/copyInterpretationState'
import postFinalizeAllele from './interpretation/actions/postFinalizeAllele'
import { testUiConfig, testSidebarOrderByNull } from '../../../fixtures/testData'

const EMPTY_EVALUATION = {
    prediction: {
        comment: ''
    },
    frequency: {
        comment: ''
    },
    external: {
        comment: ''
    },
    classification: {
        comment: ''
    },
    reference: {
        comment: ''
    },
    similar: {
        comment: ''
    }
}

let cerebral = null

// page is confused regarding jest's jsdom window mock
page.configure({ window: window })

describe('Handling of allele state', () => {
    beforeEach(() => {
        mock.setup()
        cerebral = CerebralTest(RootModule(false), {})
        cerebral.controller.addModule(
            'test',
            new Module({
                state: {},
                signals: {
                    prepareInterpretationState,
                    reuseAlleleAssessmentClicked,
                    finishConfirmationClicked,
                    postFinalizeAllele: [postFinalizeAllele, { success: [], error: [] }],
                    setReferenceAssessment: [setReferenceAssessment],
                    copyInterpretationState: [copyInterpretationState]
                }
            })
        )
    })

    afterEach(() => mock.teardown())

    it('handles assessments/reports: no existing, new, new outdated and new with old', async () => {
        // We need to make sure all expects in the API mocks are called
        expect.assertions(27)

        cerebral.setState('app.config', testUiConfig)
        cerebral.setState('app.config.classification.options', [
            {
                name: 'Class 3',
                value: '3',
                outdated_after_days: 180
            }
        ])
        cerebral.setState(
            'app.config.user.user_config.workflows.allele.finalize_requirements.workflow_status',
            ['Not ready', 'Interpretation', 'Review', 'Medical review']
        )
        cerebral.setState('app.user', {
            id: 1
        })
        // AlleleAssessments
        // allele 1: not existing - Should be initialized for editing
        // allele 2: new existing - Should be reused
        // allele 3: new existing, outdated - Should be copied into state, not reused
        // allele 4: new existing, with already old copied - Should be reused, previous data cleaned out

        // ReferenceAssessments
        // allele 1, reference 1: new existing - Should be reused
        // allele 1, reference 2: new existing, with old content - Should be reused, previous data cleaned out
        // allele 1, reference 3: new existing, with existing content by user -> Should be reused, previous data cleaned out
        // allele 2, reference 1: new existing, alleleassessment reused -> Should be reused

        // AlleleReport
        // allele 1: not existing - Should be initialized for editing
        // allele 2: new existing - Should be copied
        // allele 3: same existing - State should be left intact
        // allele 4: new existing, with already old copied - Should be copied

        cerebral.setState('views.workflows', {
            id: 1,
            alleleSidebar: {
                callerTypeSelected: 'snv',
                orderBy: testSidebarOrderByNull
            },
            type: 'allele',
            data: {
                interpretations: [
                    {
                        id: 1,
                        user: {
                            id: 1
                        },
                        workflow_status: 'Interpretation',
                        status: 'Ongoing',
                        // allele_ids: [1, 2, 3, 4],
                        state: {
                            allele: {
                                1: {
                                    allele_id: 1,
                                    caller_type: 'snv',
                                    referenceassessments: [
                                        {
                                            reference_id: 2,
                                            allele_id: 1,
                                            reuse: false,
                                            evaluation: {
                                                key: 'SHOULD BE GONE'
                                            },
                                            reuseCheckedId: 1
                                        },
                                        {
                                            reference_id: 3,
                                            allele_id: 1,
                                            evaluation: {
                                                key: 'SHOULD BE GONE'
                                            }
                                        }
                                    ]
                                },
                                3: {
                                    allele_id: 3,
                                    caller_type: 'snv',
                                    allelereport: {
                                        evaluation: { key: 'SHOULD BE KEPT' },
                                        copiedFromId: 3
                                    }
                                },
                                4: {
                                    allele_id: 4,
                                    caller_type: 'snv',
                                    alleleassessment: {
                                        reuseCheckedId: 3,
                                        reuse: false,
                                        evaluation: {
                                            key: 'SHOULD BE GONE'
                                        },
                                        classification: 'SHOULD BE GONE'
                                    },
                                    allelereport: {
                                        evaluation: { key: 'SHOULD BE REPLACED' },
                                        copiedFromId: 1
                                    },
                                    referenceassessments: [
                                        {
                                            reference_id: 1,
                                            allele_id: 4,
                                            evaluation: {
                                                key: 'ALLELEASSESSMENT REUSED -> SHOULD BE GONE'
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        user_state: {}
                    }
                ]
            },
            selectedGenepanel: {
                name: 'test',
                version: 'v01'
            },
            interpretation: {
                data: {
                    alleles: {
                        1: {
                            annotation: {
                                annotation_id: 1,
                                references: [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }],
                                frequencies: {},
                                external: {
                                    HGMD: null,
                                    CLINVAR: null
                                }
                            },
                            id: 1,
                            caller_type: 'snv',
                            reference_assessments: [
                                {
                                    id: 1,
                                    reference_id: 1,
                                    allele_id: 1,
                                    evaluation: { case: 'NEW' }
                                },
                                {
                                    id: 2,
                                    reference_id: 2,
                                    allele_id: 1,
                                    evaluation: { case: 'NEW WITH OLD' }
                                },
                                {
                                    id: 3,
                                    reference_id: 3,
                                    allele_id: 1,
                                    evaluation: { case: 'NEW WITH USER CONTENT' }
                                }
                            ],
                            tags: [],
                            formatted: {
                                display: 'test allele 1',
                                inheritance: 'AD'
                            }
                        },
                        2: {
                            annotation: {
                                annotation_id: 2,
                                references: [{ id: 1 }],
                                frequencies: {},
                                external: {
                                    HGMD: null,
                                    CLINVAR: null
                                }
                            },
                            id: 2,
                            caller_type: 'snv',
                            allele_assessment: {
                                evaluation: { case: 'NEW' },
                                classification: '3',
                                id: 2,
                                seconds_since_update: 1
                            },
                            allele_report: {
                                id: 2,
                                evaluation: { case: 'NEW' }
                            },
                            reference_assessments: [
                                {
                                    id: 4,
                                    reference_id: 1,
                                    allele_id: 2,
                                    evaluation: { case: 'ALLELEASSESSMENT IS REUSED' }
                                }
                            ],
                            tags: [],
                            formatted: {
                                display: 'test allele 2',
                                inheritance: 'AD'
                            }
                        },
                        3: {
                            annotation: {
                                annotation_id: 3,
                                references: [{ id: 1 }],
                                frequencies: {},
                                external: {
                                    HGMD: null,
                                    CLINVAR: null
                                }
                            },
                            id: 3,
                            caller_type: 'snv',
                            allele_report: {
                                id: 3,
                                evaluation: { case: 'SAME' }
                            },
                            allele_assessment: {
                                evaluation: { case: 'NEW OUTDATED' },
                                classification: '3',
                                id: 3,
                                seconds_since_update: 180 * 3600 * 24 + 1
                            },
                            tags: [],
                            formatted: {
                                display: 'test allele 3',
                                inheritance: 'AD'
                            }
                        },
                        4: {
                            annotation: {
                                annotation_id: 4,
                                references: [{ id: 1 }],
                                frequencies: {},
                                external: {
                                    HGMD: null,
                                    CLINVAR: null
                                }
                            },
                            id: 4,
                            caller_type: 'snv',
                            allele_report: {
                                id: 4,
                                evaluation: { case: 'NEW WITH OLD' }
                            },
                            allele_assessment: {
                                evaluation: { case: 'NEW WITH OLD' },
                                classification: '3',
                                id: 4,
                                seconds_since_update: 1
                            },
                            tags: [],
                            formatted: {
                                display: 'test allele 4',
                                inheritance: 'AD'
                            }
                        }
                    },
                    references: [{ id: 1 }, { id: 2 }, { id: 3 }],
                    filteredAlleleIds: {
                        allele_ids: [1, 2, 3, 4],
                        excluded_alleles_by_caller_type: {
                            snv: {},
                            cnv: {}
                        }
                    }
                },
                isOngoing: true,
                selectedId: 1
            }
        })
        await cerebral.runSignal('test.copyInterpretationState', {})
        let result = await cerebral.runSignal('test.prepareInterpretationState', {})
        let state = result.state

        let interpretationState = state.views.workflows.interpretation.state
        // Allele 1:
        let alleleState1 = interpretationState.allele['1']

        // AlleleAssessment: Initalized for editing
        expect(alleleState1.alleleassessment.reuse).toBeUndefined()
        expect(alleleState1.alleleassessment.evaluation).toEqual(
            jasmine.objectContaining(EMPTY_EVALUATION)
        )
        // ReferenceAssessment
        expect(alleleState1.referenceassessments).toEqual(
            jasmine.arrayContaining([
                {
                    reference_id: 1,
                    allele_id: 1,
                    reuse: true,
                    id: 1,
                    reuseCheckedId: 1
                },
                {
                    reference_id: 2,
                    allele_id: 1,
                    reuse: true,
                    id: 2,
                    reuseCheckedId: 2
                },
                {
                    reference_id: 3,
                    allele_id: 1,
                    reuse: true,
                    id: 3,
                    reuseCheckedId: 3
                }
            ])
        )
        // AlleleReport
        expect(alleleState1.allelereport).toEqual({ evaluation: { comment: '' } })

        // Allele 2
        let alleleState2 = interpretationState.allele['2']

        // AlleleAssessment: Should be reused
        expect(alleleState2.alleleassessment).toEqual({
            allele_id: 2,
            reuse: true,
            reuseCheckedId: 2
        })
        // ReferenceAssessment: Should be reused
        expect(alleleState2.referenceassessments).toEqual([
            {
                reference_id: 1,
                allele_id: 2,
                reuse: true,
                id: 4,
                reuseCheckedId: 4
            }
        ])

        // AlleleReport: New, should be copied
        expect(alleleState2.allelereport).toEqual({
            copiedFromId: 2,
            evaluation: { case: 'NEW' }
        })

        // Allele 3
        const alleleState3 = interpretationState.allele['3']

        // AlleleAssessment: Should be reused
        expect(alleleState3.alleleassessment.reuse).toBe(true)
        expect(alleleState3.alleleassessment.reuseCheckedId).toBe(3)

        // AlleleReport: Same id, should be kept
        expect(alleleState3.allelereport).toEqual({
            evaluation: { key: 'SHOULD BE KEPT' },
            copiedFromId: 3
        })

        // Re-evaluate outdated assessment
        let reuseToggleResult = await cerebral.runSignal('test.reuseAlleleAssessmentClicked', {
            alleleId: 3
        })
        // Allele 3 should now be not reused, existing assessment copied in with classification reset
        const alleleState3v2 =
            reuseToggleResult.state.views.workflows.interpretation.state.allele['3']
        expect(alleleState3v2.alleleassessment.reuse).toBe(false)
        expect(alleleState3v2.alleleassessment.evaluation.case).toBe('NEW OUTDATED')
        expect(alleleState3v2.alleleassessment.evaluation.classification.comment).toBe('')
        expect(alleleState3v2.alleleassessment.classification).toBe(null)

        // ReferenceAssessment:
        expect(alleleState3v2.referenceassessments).toEqual([])

        // Allele 4
        const alleleState4 = interpretationState.allele['4']

        // AlleleAssessment: Should be reused, existing content cleaned out
        expect(alleleState4.alleleassessment).toEqual({
            allele_id: 4,
            reuse: true,
            reuseCheckedId: 4
        })

        // ReferenceAssessment
        expect(alleleState4.referenceassessments).toEqual([])

        // AlleleReport: New, already copied before
        expect(alleleState4.allelereport).toEqual({
            evaluation: { case: 'NEW WITH OLD' },
            copiedFromId: 4
        })

        // Allele 2 again
        // Reevaluate then reuse again
        result = await cerebral.runSignal('test.reuseAlleleAssessmentClicked', {
            alleleId: 2
        })
        state = result.state
        interpretationState = state.views.workflows.interpretation.state
        // Allele 2 should now be not reused, existing assessment copied in
        alleleState2 = interpretationState.allele['2']
        expect(alleleState2.alleleassessment.reuse).toBe(false)
        expect(alleleState2.alleleassessment.evaluation.case).toBe('NEW')
        expect(alleleState2.alleleassessment.classification).toBe(null)

        result = await cerebral.runSignal('test.reuseAlleleAssessmentClicked', { alleleId: 2 })
        state = result.state
        interpretationState = state.views.workflows.interpretation.state
        // Allele 2 should now be reused
        alleleState2 = interpretationState.allele['2']
        expect(alleleState2.alleleassessment).toEqual({
            allele_id: 2,
            reuse: true,
            reuseCheckedId: 2
        })

        const evaluation = { key: 'USER CONTENT' }
        result = await cerebral.runSignal('test.setReferenceAssessment', {
            alleleId: 1,
            referenceId: 3,
            evaluation
        })

        state = result.state
        const alleleState = state.views.workflows.interpretation.state.allele['1']
        expect(alleleState.referenceassessments).toEqual(
            jasmine.arrayContaining([
                {
                    reference_id: 3,
                    allele_id: 1,
                    reuse: false,
                    reuseCheckedId: 3,
                    evaluation
                }
            ])
        )
        // We now want to finalize and check the data sent to API.

        // We need to classify all variants first
        cerebral.setState(
            'views.workflows.interpretation.state.allele.1.alleleassessment.classification',
            '1'
        )
        cerebral.setState(
            'views.workflows.interpretation.state.allele.2.alleleassessment.classification',
            '3'
        )
        cerebral.setState(
            'views.workflows.interpretation.state.allele.3.alleleassessment.classification',
            '3'
        )

        // Modify one AlleleReport to simluate user change
        cerebral.setState(
            'views.workflows.interpretation.state.allele.2.allelereport.evaluation.case',
            'CHANGED'
        )

        mock.error((err) => {
            throw err
        })
        mock.patch('/api/v1/workflows/alleles/1/interpretations/1/', (req, res) => {
            return res.status(200)
        })

        mock.post('/api/v1/workflows/alleles/1/actions/finalizeallele/', (req, res) => {
            const response = res
                .status(200)
                .header('Content-Type', 'application/json')
                .body(
                    JSON.stringify({
                        alleleassessment: { id: 'dummy' },
                        allelereport: { id: 'dummy' }
                    })
                )
            const body = JSON.parse(req.body())
            if (body.allele_id === 1) {
                expect(body).toEqual({
                    allele_id: 1,
                    alleleassessment: {
                        allele_id: 1,
                        attachment_ids: [],
                        classification: '1',
                        evaluation: {
                            acmg: { included: [], suggested: [] },
                            classification: { comment: '' },
                            external: { comment: '' },
                            frequency: { comment: '' },
                            prediction: { comment: '' },
                            reference: { comment: '' },
                            similar: { comment: '' }
                        },
                        reuse: false
                    },
                    allelereport: { allele_id: 1, evaluation: { comment: '' }, reuse: false },
                    annotation_id: 1,
                    custom_annotation_id: null,
                    referenceassessments: [
                        {
                            allele_id: 1,
                            id: 2,
                            reference_id: 2
                        },
                        {
                            allele_id: 1,
                            evaluation: { key: 'USER CONTENT' },
                            reference_id: 3
                        },
                        {
                            allele_id: 1,
                            id: 1,
                            reference_id: 1
                        }
                    ]
                })
                return response
            } else if (body.allele_id === 2) {
                expect(body).toEqual({
                    allele_id: 2,
                    alleleassessment: {
                        allele_id: 2,
                        presented_alleleassessment_id: 2,
                        reuse: true
                    },
                    allelereport: {
                        allele_id: 2,
                        evaluation: { case: 'CHANGED' },
                        presented_allelereport_id: 2,
                        reuse: false
                    },
                    annotation_id: 2,
                    custom_annotation_id: null,
                    referenceassessments: [
                        {
                            allele_id: 2,
                            id: 4,
                            reference_id: 1
                        }
                    ]
                })
                return response
            } else if (body.allele_id === 3) {
                expect(body).toEqual({
                    allele_id: 3,
                    alleleassessment: {
                        allele_id: 3,
                        classification: '3',
                        evaluation: {
                            acmg: { included: [], suggested: [] },
                            case: 'NEW OUTDATED',
                            classification: { comment: '' },
                            external: { comment: '' },
                            frequency: { comment: '' },
                            prediction: { comment: '' },
                            reference: { comment: '' },
                            similar: { comment: '' }
                        },
                        presented_alleleassessment_id: 3,
                        reuse: false
                    },
                    allelereport: {
                        allele_id: 3,
                        evaluation: { key: 'SHOULD BE KEPT' },
                        presented_allelereport_id: 3,
                        reuse: false
                    },
                    annotation_id: 3,
                    custom_annotation_id: null,
                    referenceassessments: []
                })
                return response
            } else if (body.allele_id === 4) {
                expect(body).toEqual({
                    allele_id: 4,
                    alleleassessment: {
                        allele_id: 4,
                        presented_alleleassessment_id: 4,
                        reuse: true
                    },
                    allelereport: {
                        allele_id: 4,
                        presented_allelereport_id: 4,
                        reuse: true
                    },
                    annotation_id: 4,
                    custom_annotation_id: null,
                    referenceassessments: []
                })
                return response
            }
        })

        // Rest is checked in API mocks

        for (let alleleId of [1, 2, 3, 4]) {
            await cerebral.runSignal('test.postFinalizeAllele', {
                alleleId
            })
        }
    })

    it('migrates old state correctly', async () => {
        cerebral.setState('app.config', {
            classification: {
                options: [
                    {
                        name: 'Class 5',
                        value: '5',
                        outdated_after_days: 180,
                        include_report: true
                    },
                    {
                        name: 'Class 4',
                        value: '4',
                        outdated_after_days: 180,
                        include_report: true
                    }
                ]
            },
            user: { user_config: {} },
            frequencies: {
                groups: {
                    external: {
                        GNOMAD_GENOMES: ['G', 'AFR', 'AMR', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS'],
                        GNOMAD_EXOMES: ['G', 'AFR', 'AMR', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS']
                    },
                    internal: {
                        inDB: ['OUSWES']
                    }
                }
            }
        })

        // Real state from pre-1.1
        const MIGRATION_BASE = {
            allele: {
                '584': {
                    report: {
                        included: true
                    },
                    allele_id: 584,
                    allelereport: {
                        evaluation: {
                            comment: 'TEST'
                        }
                    },
                    alleleassessment: {
                        reuse: true,
                        evaluation: {
                            acmg: {
                                included: [],
                                suggested: [
                                    {
                                        op: '$in',
                                        code: 'REQ_GP_last_exon_not_important',
                                        match: ['LENI'],
                                        source: 'genepanel.last_exon_important'
                                    }
                                ],
                                suggested_classification: null
                            },
                            external: {
                                comment: ''
                            },
                            frequency: {
                                comment: 'TEST'
                            },
                            reference: {
                                comment: ''
                            },
                            prediction: {
                                comment: ''
                            },
                            classification: {
                                comment: 'TEST'
                            }
                        },
                        attachment_ids: [],
                        classification: '5'
                    },
                    referenceassessments: [
                        {
                            id: 1,
                            allele_id: 584,
                            reference_id: 521
                        }
                    ],
                    alleleReportCopiedFromId: 1,
                    presented_allelereport_id: 1,
                    alleleAssessmentCopiedFromId: 1,
                    presented_alleleassessment_id: 1,
                    autoReuseAlleleAssessmentCheckedId: 1
                },
                '585': {
                    allele_id: 585,
                    allelereport: {
                        evaluation: {
                            comment: ''
                        }
                    },
                    alleleassessment: {
                        reuse: false,
                        evaluation: {
                            acmg: {
                                included: [],
                                suggested: [
                                    {
                                        op: '$in',
                                        code: 'REQ_GP_last_exon_not_important',
                                        match: ['LENI'],
                                        source: 'genepanel.last_exon_important'
                                    },
                                    {
                                        op: null,
                                        code: 'PVS1',
                                        match: null,
                                        source: null
                                    },
                                    {
                                        op: null,
                                        code: 'PPxPM2',
                                        match: null,
                                        source: null
                                    }
                                ],
                                suggested_classification: null
                            },
                            external: {
                                comment: ''
                            },
                            frequency: {
                                comment: ''
                            },
                            reference: {
                                comment: ''
                            },
                            prediction: {
                                comment: ''
                            },
                            classification: {
                                comment: ''
                            }
                        },
                        attachment_ids: [],
                        classification: null
                    },
                    referenceassessments: [
                        {
                            allele_id: 585,
                            evaluation: {},
                            reference_id: 363
                        },
                        {
                            allele_id: 585,
                            evaluation: {},
                            reference_id: 229
                        }
                    ]
                },
                '586': {
                    allele_id: 586,
                    allelereport: {
                        evaluation: {
                            comment: ''
                        }
                    },
                    alleleassessment: {
                        reuse: false,
                        evaluation: {
                            acmg: {
                                included: [],
                                suggested: []
                            },
                            external: {
                                comment: ''
                            },
                            frequency: {
                                comment: ''
                            },
                            reference: {
                                comment: ''
                            },
                            prediction: {
                                comment: ''
                            },
                            classification: {
                                comment: ''
                            }
                        },
                        attachment_ids: [],
                        classification: null
                    },
                    referenceassessments: []
                },
                '589': {
                    report: {
                        included: true
                    },
                    allele_id: 589,
                    allelereport: {
                        evaluation: {
                            comment: 'TEST2'
                        }
                    },
                    alleleassessment: {
                        reuse: false,
                        evaluation: {
                            acmg: {
                                included: [],
                                suggested: [
                                    {
                                        op: '$in',
                                        code: 'REQ_GP_last_exon_not_important',
                                        match: ['LENI'],
                                        source: 'genepanel.last_exon_important'
                                    }
                                ],
                                suggested_classification: null
                            },
                            external: {
                                comment: ''
                            },
                            frequency: {
                                comment: ''
                            },
                            reference: {
                                comment: ''
                            },
                            prediction: {
                                comment: ''
                            },
                            classification: {
                                comment: 'TEST2'
                            }
                        },
                        attachment_ids: [],
                        classification: '4'
                    },
                    referenceassessments: [],
                    alleleReportCopiedFromId: 2,
                    presented_allelereport_id: 2,
                    alleleAssessmentCopiedFromId: 2,
                    presented_alleleassessment_id: 2,
                    autoReuseAlleleAssessmentCheckedId: 2
                }
            }
        }

        cerebral.setState('views.workflows', {
            id: 1,
            type: 'analysis',
            alleleSidebar: {
                callerTypeSelected: 'snv'
            },
            interpretation: {
                data: {
                    alleles: {
                        584: {
                            formatted: {
                                display: 'test allele 1'
                            },
                            allele_assessment: {
                                id: 1,
                                seconds_since_update: 1,
                                classification: '5'
                            },
                            reference_assessments: [
                                {
                                    id: 1,
                                    allele_id: 584,
                                    reference_id: 521,
                                    evaluation: { key: 'SOMETHING' }
                                }
                            ],
                            id: 584
                        },
                        585: {
                            formatted: {
                                display: 'test allele 2'
                            },
                            id: 585
                        },
                        586: {
                            formatted: {
                                display: 'test allele 3'
                            },
                            id: 586
                        },
                        589: {
                            formatted: {
                                display: 'test allele 4'
                            },
                            allele_assessment: {
                                id: 2,
                                seconds_since_update: 1,
                                classification: '5'
                            },
                            id: 589
                        }
                    },
                    references: [{ id: 1 }]
                },
                id: 1,
                status: 'Ongoing',
                filteredAlleleIds: {
                    allele_ids: [584, 585, 586, 589]
                },
                state: MIGRATION_BASE,
                userState: {}
            }
        })

        const { state } = await cerebral.runSignal('test.prepareInterpretationState', {})

        const interpretationState = state.views.workflows.interpretation.state

        // Allele 584: Was reused before migration -> should have cleaned out alleleassessment
        expect(interpretationState.allele['584']).toEqual({
            report: {
                included: true
            },
            allele_id: 584,
            allelereport: {
                copiedFromId: 1,
                evaluation: {
                    comment: 'TEST'
                }
            },
            analysis: {
                comment: '',
                notrelevant: null,
                verification: null
            },
            workflow: {
                reviewed: false
            },
            alleleassessment: {
                reuse: true,
                reuseCheckedId: 1,
                allele_id: 584
            },
            referenceassessments: [
                {
                    id: 1,
                    reuse: true,
                    allele_id: 584,
                    reuseCheckedId: 1,
                    reference_id: 521
                }
            ]
        })

        // Allele 585: Had user content, empty referenceassessments should be removed
        expect(interpretationState.allele['585']).toEqual({
            allele_id: 585,
            report: {
                included: false
            },
            allelereport: {
                evaluation: {
                    comment: ''
                }
            },
            analysis: {
                comment: '',
                verification: null,
                notrelevant: null
            },
            workflow: {
                reviewed: false
            },
            alleleassessment: {
                reuse: false,
                evaluation: {
                    acmg: {
                        included: [],
                        suggested: [
                            {
                                op: '$in',
                                code: 'REQ_GP_last_exon_not_important',
                                match: ['LENI'],
                                source: 'genepanel.last_exon_important'
                            },
                            {
                                op: null,
                                code: 'PVS1',
                                match: null,
                                source: null
                            },
                            {
                                op: null,
                                code: 'PPxPM2',
                                match: null,
                                source: null
                            }
                        ],
                        suggested_classification: null
                    },
                    external: {
                        comment: ''
                    },
                    frequency: {
                        comment: ''
                    },
                    reference: {
                        comment: ''
                    },
                    prediction: {
                        comment: ''
                    },
                    classification: {
                        comment: ''
                    },
                    similar: {
                        comment: ''
                    }
                },
                attachment_ids: [],
                classification: null
            },
            referenceassessments: []
        })

        // Allele 586: Was empty. Should be almost same
        expect(interpretationState.allele['586']).toEqual({
            allele_id: 586,
            report: {
                included: false
            },
            allelereport: {
                evaluation: {
                    comment: ''
                }
            },
            analysis: {
                comment: '',
                verification: null,
                notrelevant: null
            },
            workflow: {
                reviewed: false
            },
            alleleassessment: {
                reuse: false,
                evaluation: {
                    acmg: {
                        included: [],
                        suggested: []
                    },
                    external: {
                        comment: ''
                    },
                    frequency: {
                        comment: ''
                    },
                    reference: {
                        comment: ''
                    },
                    prediction: {
                        comment: ''
                    },
                    classification: {
                        comment: ''
                    },
                    similar: {
                        comment: ''
                    }
                },
                attachment_ids: [],
                classification: null
            },
            referenceassessments: []
        })

        // Allele 589: Has alleleassessment, but is not reused. Alleleassessment content should be kept.
        expect(interpretationState.allele['589']).toEqual({
            report: {
                included: true
            },
            allele_id: 589,
            allelereport: {
                copiedFromId: 2,
                evaluation: {
                    comment: 'TEST2'
                }
            },
            analysis: {
                comment: '',
                verification: null,
                notrelevant: null
            },
            workflow: {
                reviewed: false
            },
            alleleassessment: {
                reuse: false,
                reuseCheckedId: 2,
                evaluation: {
                    acmg: {
                        included: [],
                        suggested: [
                            {
                                op: '$in',
                                code: 'REQ_GP_last_exon_not_important',
                                match: ['LENI'],
                                source: 'genepanel.last_exon_important'
                            }
                        ],
                        suggested_classification: null
                    },
                    external: {
                        comment: ''
                    },
                    frequency: {
                        comment: ''
                    },
                    reference: {
                        comment: ''
                    },
                    prediction: {
                        comment: ''
                    },
                    classification: {
                        comment: 'TEST2'
                    },
                    similar: {
                        comment: ''
                    }
                },
                attachment_ids: [],
                classification: '4'
            },
            referenceassessments: []
        })
    })
})
