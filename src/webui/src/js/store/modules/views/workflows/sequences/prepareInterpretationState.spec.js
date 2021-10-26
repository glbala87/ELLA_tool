import { Module } from 'cerebral'
import { CerebralTest } from 'cerebral/test'
import RootModule from '../../..'
import prepareInterpretationState from './prepareInterpretationState'
import reuseAlleleAssessmentClicked from '../interpretation/signals/reuseAlleleAssessmentClicked'
import { testUiConfig, testSidebarOrderByNull } from '../../../../fixtures/testData'
import callerTypeSelectedChanged from '../alleleSidebar/signals/callerTypeSelectedChanged'

let cerebral = null

function createAlleleData(id, callerType) {
    return {
        id: id,
        caller_type: callerType,
        formatted: {
            display: 'test variant'
        },
        tags: [],
        annotation: {
            annotation_id: id,
            references: [{ id: id }],
            frequencies: {},
            external: {
                HGMD: null,
                CLINVAR: null
            }
        },
        allele_assessment: {
            evaluation: { classification: { comment: 'TEST' } },
            classification: '3',
            id: id,
            seconds_since_update: id
        },
        allele_report: {
            id: id,
            evaluation: { classification: { comment: 'TEST' } }
        },
        reference_assessments: [
            {
                id: id,
                reference_id: id,
                allele_id: id,
                evaluation: { classification: { comment: 'TEST' } }
            }
        ]
    }
}

describe('prepareInterpretationState', () => {
    beforeEach(() => {
        cerebral = CerebralTest(RootModule(false), {})
        cerebral.controller.addModule(
            'test',
            new Module({
                state: {},
                signals: {
                    prepareInterpretationState,
                    reuseAlleleAssessmentClicked,
                    callerTypeSelectedChanged
                }
            })
        )
    })

    it('gracefully handles updates to manuallyIncludedAlleleIds', async () => {
        cerebral.setState('app.config', testUiConfig)
        cerebral.setState('app.config.classification.options', [
            {
                name: 'Class 3',
                value: '3',
                outdated_after_days: 180
            }
        ])
        cerebral.setState('app.config.user.user_config', {})
        cerebral.setState('app.user', {
            id: 1
        })
        cerebral.setState('views.workflows', {
            id: 1,
            type: 'analysis',
            data: {
                interpretations: [
                    {
                        id: 1,
                        user: {
                            id: 1
                        }
                    }
                ]
            },
            interpretation: {
                data: {
                    alleles: {
                        1: createAlleleData(1, 'SNV'),
                        2: createAlleleData(2, 'SNV'),
                        4: createAlleleData(4, 'CNV'),
                        6: createAlleleData(6, 'CNV')
                    },
                    filteredAlleleIds: {
                        allele_ids: [1, 6],
                        excluded_alleles_by_caller_type: {
                            snv: {
                                testFilter: [2, 3]
                            },
                            cnv: {
                                testFilter: [4, 5]
                            }
                        }
                    }
                },
                userState: {},
                state: {},
                isOngoing: true,
                selectedId: 1
            },
            alleleSidebar: {
                callerTypeSelected: 'snv',
                orderBy: testSidebarOrderByNull
            }
        })

        // Start with one included allele (id 2) from filtered alleles
        // (when set in manuallyAddedAlleleIds it will be loaded into workflows.interpretation.data.alleles)
        let result = await cerebral.runSignal('test.prepareInterpretationState', {})
        let state = result.state

        // Open alleleassessment for allele 2 for editing
        await cerebral.runSignal('test.reuseAlleleAssessmentClicked', { alleleId: 2 })

        // Modify state's alleleassessment data
        cerebral.setState(
            'views.workflows.interpretation.state.allele.2.alleleassessment.evaluation.classification',
            {
                comment: 'UPDATED'
            }
        )

        // Copy out data for comparison later
        var alleleassessmentCopy = JSON.parse(
            JSON.stringify(
                cerebral.getState().views.workflows.interpretation.state.allele[2].alleleassessment
            )
        )

        // Remove allele from data (i.e. not manually added anymore)
        // state should be kept as is in case it's included again
        cerebral.setState('views.workflows.interpretation.data.alleles', {
            1: createAlleleData(1),
            4: createAlleleData(4),
            6: createAlleleData(6)
        })

        result = await cerebral.runSignal('test.prepareInterpretationState', {})
        state = result.state
        expect(state.views.workflows.interpretation.state.allele[2].alleleassessment).toEqual(
            alleleassessmentCopy
        )

        // Add it back in. State should still remain the same
        // (which also implies it's still {reuse: false} and not automatically reused)
        cerebral.setState('views.workflows.interpretation.data.alleles', {
            1: createAlleleData(1),
            2: createAlleleData(2),
            4: createAlleleData(4),
            6: createAlleleData(6)
        })

        result = await cerebral.runSignal('test.prepareInterpretationState', {})
        state = result.state
        expect(state.views.workflows.interpretation.state.allele[2].alleleassessment).toEqual(
            alleleassessmentCopy
        )

        result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelected: 'cnv'
        })

        expect(state.views.workflows.alleleSidebar.callerTypeSelected).toEqual('cnv')

        result = await cerebral.runSignal('test.prepareInterpretationState', {})
        state = result.state

        // Open alleleassessment for allele 4 for editing
        await cerebral.runSignal('test.reuseAlleleAssessmentClicked', { alleleId: 4 })

        // Modify state's alleleassessment data
        cerebral.setState(
            'views.workflows.interpretation.state.allele.4.alleleassessment.evaluation.classification',
            {
                comment: 'UPDATED'
            }
        )

        // Copy out data for comparison later
        alleleassessmentCopy = JSON.parse(
            JSON.stringify(
                cerebral.getState().views.workflows.interpretation.state.allele[4].alleleassessment
            )
        )

        // Remove allele from data (i.e. not manually added anymore)
        // state should be kept as is in case it's included again
        cerebral.setState('views.workflows.interpretation.data.alleles', {
            1: createAlleleData(1),
            2: createAlleleData(2),
            6: createAlleleData(6)
        })

        result = await cerebral.runSignal('test.prepareInterpretationState', {})
        state = result.state
        expect(state.views.workflows.interpretation.state.allele[4].alleleassessment).toEqual(
            alleleassessmentCopy
        )

        // Add it back in. State should still remain the same
        // (which also implies it's still {reuse: false} and not automatically reused)
        cerebral.setState('views.workflows.interpretation.data.alleles', {
            1: createAlleleData(1),
            2: createAlleleData(2),
            4: createAlleleData(4),
            6: createAlleleData(6)
        })

        result = await cerebral.runSignal('test.prepareInterpretationState', {})
        state = result.state
        expect(state.views.workflows.interpretation.state.allele[4].alleleassessment).toEqual(
            alleleassessmentCopy
        )
    })
})
