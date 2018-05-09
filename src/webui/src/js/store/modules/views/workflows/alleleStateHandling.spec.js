import mock from 'xhr-mock'
import Devtools from 'cerebral/devtools'
import { CerebralTest } from 'cerebral/test'
import RootModule from '../../'
import { Module } from 'cerebral'
import prepareInterpretationState from './sequences/prepareInterpretationState'
import reuseAlleleAssessmentClicked from './interpretation/signals/reuseAlleleAssessmentClicked'
import finishConfirmationClicked from './signals/finishConfirmationClicked'

/*

Tests:

- No existing alleleassessments
- Has existing alleleassessment - not outdated (- first time copy, next time user content is kept)
- Has existing alleleassessment - outdated (- first time copy, next time user content is kept)
- Has existing alleleassessment - already copied old alleleassessment to state

- No existing allelereport
- Has existing allelereport - first time copy, next time user content is kept
- Has existing allelereport - already copied old allelereport to state

- No referenceassessments
- Has existing referenceassessments
- Has existing referenceassessments - already reused old referenceassessments

- Migrations

- checkAddRemoveAlleleToReport

prepareInterpretationState,
(reuseAlleleAssessmentClicked),
updateReferenceAssessment,

"always" finishWorkflow => check POST data

*/

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
                    finishConfirmationClicked
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
        // Allele 1: no existing - Should be initialized for editing
        // Allele 2: new existing - Should be reused
        // Allele 3: new existing, outdated - Should not be reused, data copied in to state
        // Allele 4: new existing, with already old copied - Should be reused, previous data cleaned out
        cerebral.setState('views.workflows', {
            id: 1,
            type: 'allele',
            data: {
                alleles: {
                    1: {
                        annotation: {
                            annotation_id: 1,
                            references: [{ id: 1 }]
                        },
                        id: 1
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
                        }
                    },
                    3: {
                        annotation: {
                            annotation_id: 3,
                            references: [{ id: 1 }]
                        },
                        id: 3,
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
                        allele_assessment: {
                            evaluation: { case: 'NEW WITH OLD' },
                            classification: '3',
                            id: 4,
                            seconds_since_update: 1
                        }
                    }
                },
                references: []
            },
            interpretation: {
                selected: {
                    id: 1,
                    status: 'Ongoing',
                    allele_ids: [1, 2, 3, 4],
                    state: {
                        allele: {
                            4: {
                                alleleassessment: {
                                    reuseCheckedId: 3,
                                    reuse: false,
                                    evaluation: {
                                        key: 'SHOULD BE GONE'
                                    },
                                    classification: 'SHOULD BE GONE'
                                }
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
                    // Allele 1: Initalized for editing
                    const alleleState1 = interpretationState.allele['1']
                    expect(alleleState1.alleleassessment.reuse).toBeUndefined()
                    expect(alleleState1.alleleassessment.evaluation).toEqual(
                        jasmine.objectContaining(EMPTY_EVALUATION)
                    )

                    // Allele 2: Should be reused
                    const alleleState2 = interpretationState.allele['2']
                    expect(alleleState2.alleleassessment).toEqual({
                        allele_id: 2,
                        reuse: true,
                        reuseCheckedId: 2
                    })

                    // Allele 3: Should not be reused, existing copied in
                    const alleleState3 = interpretationState.allele['3']
                    expect(alleleState3.alleleassessment.reuse).toBe(false)
                    expect(alleleState3.alleleassessment.reuseCheckedId).toBe(3)
                    expect(alleleState3.alleleassessment.evaluation.case).toBe('NEW OUTDATED')
                    expect(alleleState3.alleleassessment.evaluation).toEqual(
                        jasmine.objectContaining(EMPTY_EVALUATION)
                    )
                    expect(alleleState3.alleleassessment.classification).toBe('3')

                    // Allele 4: Should be reused, existing content cleaned out
                    const alleleState4 = interpretationState.allele['4']
                    expect(alleleState4.alleleassessment).toEqual({
                        allele_id: 4,
                        reuse: true,
                        reuseCheckedId: 4
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
                    // We now want to finalize and check the data sent to API.
                    // We need to classify all variants first
                    cerebral.setState(
                        'views.workflows.interpretation.selected.state.allele.1.alleleassessment.classification',
                        '1'
                    )

                    mock.patch('/api/v1/workflows/alleles/1/interpretations/1/', (req, res) => {
                        return res.status(200)
                    })

                    mock.post('/api/v1/workflows/alleles/1/actions/finalize/', (req, res) => {
                        const body = JSON.parse(req.body())
                        console.log(body.alleleassessments[1])
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
