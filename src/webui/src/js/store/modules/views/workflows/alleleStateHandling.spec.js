import mock from 'xhr-mock'
import Devtools from 'cerebral/devtools'
import { CerebralTest } from 'cerebral/test'
import RootModule from '../../'
import { Module } from 'cerebral'
import prepareInterpretationState from './sequences/prepareInterpretationState'
import reuseAlleleAssessmentClicked from './interpretation/signals/reuseAlleleAssessmentClicked'
import finishConfirmationClicked from './signals/finishConfirmationClicked'
import setReferenceAssessment from './interpretation/actions/setReferenceAssessment'

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
    }
}

let cerebral = null

describe('Handling of allele state', () => {
    beforeAll(() =>
        (cerebral = CerebralTest(RootModule(false), {
            devtools: Devtools({
                host: '193.157.231.138:9595'
            })
        })))

    beforeEach(() => mock.setup())
    afterEach(() => mock.teardown())

    it('handles assessments/reports: no existing, new, new outdated and new with old', () => {
        cerebral.controller.addModule(
            'test',
            new Module({
                state: {},
                signals: {
                    prepareInterpretationState,
                    reuseAlleleAssessmentClicked,
                    finishConfirmationClicked,
                    setReferenceAssessment: [setReferenceAssessment]
                }
            })
        )

        cerebral.setState('app.config', {
            classification: {
                options: [
                    {
                        name: 'Class 3',
                        value: '3',
                        outdated_after_days: 180
                    }
                ]
            },
            user: { user_config: {} }
        })
        // AlleleAssessments
        // allele 1: no existing - Should be initialized for editing
        // allele 2: new existing - Should be reused
        // allele 3: new existing, outdated - Should not be reused, data copied in to state
        // allele 4: new existing, with already old copied - Should be reused, previous data cleaned out

        // ReferenceAssessments
        // allele 1, reference 1: new existing - Should be reused
        // allele 1, reference 2: new existing, with old content - Should be reused, previous data cleaned out
        // allele 1, reference 3: new existing, with existing content by user -> Should be reused, previous data cleaned out
        // allele 2, reference 1: new existing, alleleassessment reused -> empty list in state

        // AlleleReport
        // allele 1: no existing - Should be initialized for editing
        // allele 2: new existing - Should be copied
        // allele 3: same existing - State should be left intact
        // allele 4: new existing, with already old copied - Should be copied

        cerebral.setState('views.workflows', {
            id: 1,
            type: 'allele',
            data: {
                alleles: {
                    1: {
                        annotation: {
                            annotation_id: 1,
                            references: [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }]
                        },
                        id: 1,
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
                        ]
                    },
                    2: {
                        annotation: {
                            annotation_id: 2,
                            references: [{ id: 1 }]
                        },
                        id: 2,
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
                        ]
                    },
                    3: {
                        annotation: {
                            annotation_id: 3,
                            references: [{ id: 1 }]
                        },
                        id: 3,
                        allele_report: {
                            id: 3,
                            evaluation: { case: 'SAME' }
                        },
                        allele_assessment: {
                            evaluation: { case: 'NEW OUTDATED' },
                            classification: '3',
                            id: 3,
                            seconds_since_update: 180 * 3600 * 24 + 1
                        }
                    },
                    4: {
                        annotation: {
                            annotation_id: 4,
                            references: [{ id: 1 }]
                        },
                        id: 4,
                        allele_report: {
                            id: 4,
                            evaluation: { case: 'NEW WITH OLD' }
                        },
                        allele_assessment: {
                            evaluation: { case: 'NEW WITH OLD' },
                            classification: '3',
                            id: 4,
                            seconds_since_update: 1
                        }
                    }
                },
                references: [{ id: 1 }, { id: 2 }, { id: 3 }]
            },
            interpretation: {
                selected: {
                    id: 1,
                    status: 'Ongoing',
                    allele_ids: [1, 2, 3, 4],
                    state: {
                        allele: {
                            1: {
                                allele_id: 1,
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
                                allelereport: {
                                    evaluation: { key: 'SHOULD BE KEPT' },
                                    copiedFromId: 3
                                }
                            },
                            4: {
                                allele_id: 4,
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
            }
        })

        return (
            cerebral
                .runSignal('test.prepareInterpretationState', {})
                .then(({ state }) => {
                    const interpretationState = state.views.workflows.interpretation.selected.state
                    // Allele 1:
                    const alleleState1 = interpretationState.allele['1']

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
                    const alleleState2 = interpretationState.allele['2']

                    // AlleleAssessment: Should be reused
                    expect(alleleState2.alleleassessment).toEqual({
                        allele_id: 2,
                        reuse: true,
                        reuseCheckedId: 2
                    })
                    // ReferenceAssessment: Should be empty (alleleassessment reused)
                    expect(alleleState2.referenceassessments).toEqual([])

                    // AlleleReport: New, should be copied
                    expect(alleleState2.allelereport).toEqual({
                        copiedFromId: 2,
                        evaluation: { case: 'NEW' }
                    })

                    // Allele 3
                    const alleleState3 = interpretationState.allele['3']

                    // AlleleAssessment: Should not be reused, existing copied in
                    expect(alleleState3.alleleassessment.reuse).toBe(false)
                    expect(alleleState3.alleleassessment.reuseCheckedId).toBe(3)
                    expect(alleleState3.alleleassessment.evaluation.case).toBe('NEW OUTDATED')
                    expect(alleleState3.alleleassessment.evaluation).toEqual(
                        jasmine.objectContaining(EMPTY_EVALUATION)
                    )
                    expect(alleleState3.alleleassessment.classification).toBe('3')

                    // ReferenceAssessment:
                    expect(alleleState3.referenceassessments).toEqual([])

                    // AlleleReport: Same id, should be kept
                    expect(alleleState3.allelereport).toEqual({
                        evaluation: { key: 'SHOULD BE KEPT' },
                        copiedFromId: 3
                    })

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
                })
                // Reevaluate then reuse again
                .then(() => {
                    return cerebral
                        .runSignal('test.reuseAlleleAssessmentClicked', { alleleId: 2 })
                        .then(({ state }) => {
                            const interpretationState =
                                state.views.workflows.interpretation.selected.state
                            // Allele 2 should now be not reused, existing assessment copied in
                            const alleleState2 = interpretationState.allele['2']
                            expect(alleleState2.alleleassessment.reuse).toBe(false)
                            expect(alleleState2.alleleassessment.evaluation.case).toBe('NEW')
                            expect(alleleState2.alleleassessment.classification).toBe('3')
                        })
                })
                .then(() => {
                    return cerebral
                        .runSignal('test.reuseAlleleAssessmentClicked', { alleleId: 2 })
                        .then(({ state }) => {
                            const interpretationState =
                                state.views.workflows.interpretation.selected.state
                            // Allele 2 should now be reused
                            const alleleState2 = interpretationState.allele['2']
                            expect(alleleState2.alleleassessment).toEqual({
                                allele_id: 2,
                                reuse: true,
                                reuseCheckedId: 2
                            })
                        })
                })
                .then(() => {
                    const evaluation = { key: 'USER CONTENT' }
                    return cerebral
                        .runSignal('test.setReferenceAssessment', {
                            alleleId: 1,
                            referenceId: 3,
                            evaluation
                        })
                        .then(({ state }) => {
                            const alleleState =
                                state.views.workflows.interpretation.selected.state.allele['1']
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
                        })
                })
                .then(() => {
                    // We now want to finalize and check the data sent to API.

                    // We need to classify all variants first
                    cerebral.setState(
                        'views.workflows.interpretation.selected.state.allele.1.alleleassessment.classification',
                        '1'
                    )

                    // Modify one AlleleReport to simluate user change
                    cerebral.setState(
                        'views.workflows.interpretation.selected.state.allele.2.allelereport.evaluation.case',
                        'CHANGED'
                    )

                    mock.patch('/api/v1/workflows/alleles/1/interpretations/1/', (req, res) => {
                        return res.status(200)
                    })

                    mock.post('/api/v1/workflows/alleles/1/actions/finalize/', (req, res) => {
                        const body = JSON.parse(req.body())
                        expect(body.alleleassessments.length).toBe(4)
                        for (const alleleAssessment of body.alleleassessments) {
                            if (alleleAssessment.allele_id === 1) {
                                expect(alleleAssessment.classification).toBe('1')
                                expect(alleleAssessment.reuse).toBe(false)
                            }
                            if (alleleAssessment.allele_id === 2) {
                                expect(alleleAssessment.classification).toBeUndefined()
                                expect(alleleAssessment.evaluation).toBeUndefined()
                                expect(alleleAssessment.reuse).toBe(true)
                            }
                            if (alleleAssessment.allele_id === 3) {
                                expect(alleleAssessment.classification).toBe('3')
                                expect(alleleAssessment.evaluation.case).toBe('NEW OUTDATED')
                                expect(alleleAssessment.reuse).toBe(false)
                            }
                            if (alleleAssessment.allele_id === 4) {
                                expect(alleleAssessment.classification).toBeUndefined()
                                expect(alleleAssessment.evaluation).toBeUndefined()
                                expect(alleleAssessment.reuse).toBe(true)
                            }
                        }

                        expect(body.referenceassessments).toEqual(
                            jasmine.arrayContaining([
                                {
                                    reference_id: 1,
                                    allele_id: 1,
                                    id: 1
                                },
                                {
                                    reference_id: 2,
                                    allele_id: 1,
                                    id: 2
                                },
                                {
                                    reference_id: 3,
                                    allele_id: 1,
                                    evaluation: { key: 'USER CONTENT' }
                                }
                            ])
                        )

                        expect(body.allelereports.length).toBe(4)
                        expect(body.allelereports).toEqual(
                            jasmine.arrayContaining([
                                {
                                    allele_id: 1,
                                    reuse: false,
                                    evaluation: { comment: '' }
                                },
                                {
                                    allele_id: 2,
                                    presented_allelereport_id: 2,
                                    reuse: false,
                                    alleleassessment_id: 2,
                                    evaluation: { case: 'CHANGED' }
                                },
                                {
                                    allele_id: 3,
                                    presented_allelereport_id: 3,
                                    reuse: false, // State differs from existing
                                    alleleassessment_id: 3,
                                    evaluation: { key: 'SHOULD BE KEPT' }
                                },
                                {
                                    allele_id: 4,
                                    presented_allelereport_id: 4,
                                    reuse: true,
                                    alleleassessment_id: 4
                                }
                            ])
                        )

                        return res.status(200)
                    })

                    // Everything is checked in API mock
                    return cerebral.runSignal('test.finishConfirmationClicked', {
                        workflowStatus: 'Finalized'
                    })
                })
                .catch((err) => {
                    console.error(err.message, err.stack)
                    expect(1).toBe(0)
                })
        )
    })
})
