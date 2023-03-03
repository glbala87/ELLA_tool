import { runCompute } from 'cerebral/test'

import canFinalize from './canFinalize'

const defaultConfig = {
    workflowType: 'analysis',
    workflowStatus: 'Review',
    status: 'Ongoing',
    requiredWorkflowStatus: ['Review'],
    allowTechnical: true,
    allowNotRelevant: true,
    allowUnclassified: false,
    numTechnical: 0,
    numNotRelevant: 0,
    numUnclassified: 0,
    numClassified: 0,
    numOutdated: 0
}

function createState(config) {
    config = Object.assign({}, defaultConfig, config)

    const interpretation = {
        id: 1,
        type: config.workflowType,
        status: config.status,
        workflow_status: config.workflowStatus,
        state: { allele: {} },
        user_state: {}
    }
    const alleles = {}

    let currentAlleleId = 0
    for (let i = 0; i < config.numTechnical; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: 'technical',
                notrelevant: false
            },
            alleleassessment: {}
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestTechnical id ${currentAlleleId}` }
        }
    }

    for (let i = 0; i < config.numNotRelevant; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: true
            },
            alleleassessment: {}
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestNotRelevant id ${currentAlleleId}` }
        }
    }

    for (let i = 0; i < config.numUnclassified; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            },
            alleleassessment: {}
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestUnclassified id ${currentAlleleId}` }
        }
    }

    for (let i = 0; i < config.numClassified; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            },
            alleleassessment: {
                reuse: true
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestClassified id ${currentAlleleId}` },
            allele_assessment: {
                classification: '5',
                seconds_since_update: 1
            }
        }
    }

    for (let i = 0; i < config.numOutdated; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestOutdated id ${currentAlleleId}` },
            allele_assessment: {
                classification: '5',
                seconds_since_update: 10 * 24 * 3600
            }
        }
    }

    for (let i = 0; i < config.numNotSubmitted; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            },
            alleleassessment: {
                classification: '5'
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestNotSubmitted id ${currentAlleleId}` }
        }
    }

    for (let i = 0; i < config.numNotSubmittedReused; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            },
            alleleassessment: {
                reuse: false,
                classification: '5'
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestNotSubmittedReused id ${currentAlleleId}` },
            allele_assessment: {
                classification: '5',
                seconds_since_update: 1
            }
        }
    }

    for (let i = 0; i < config.numUpdatedReportNoExisting; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            },
            alleleassessment: {},
            allelereport: {
                evaluation: { comment: 'UPDATED' }
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestUpdatedReportNoExisting id ${currentAlleleId}` }
        }
    }

    for (let i = 0; i < config.numUpdatedReport; i++) {
        currentAlleleId += 1
        interpretation.state.allele[currentAlleleId] = {
            analysis: {
                verification: null,
                notrelevant: false
            },
            alleleassessment: {
                reuse: true
            },
            allelereport: {
                evaluation: { comment: 'UPDATED' }
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestUpdatedReport id ${currentAlleleId}` },
            allele_assessment: {
                classification: '5',
                seconds_since_update: 1
            },
            allele_report: {
                evaluation: {
                    comment: 'ORIGINAL'
                }
            }
        }
    }

    return {
        app: {
            config: {
                user: {
                    user_config: {
                        workflows: {
                            analysis: {
                                finalize_requirements: {
                                    workflow_status: config.requiredWorkflowStatus,
                                    allow_unclassified: config.allowUnclassified
                                }
                            },
                            allele: {
                                finalize_requirements: {
                                    workflow_status: config.requiredWorkflowStatus
                                }
                            }
                        }
                    }
                },
                classification: {
                    options: [
                        {
                            value: '5',
                            outdated_after_days: 1,
                            name: 'Class 5'
                        }
                    ]
                }
            }
        },
        views: {
            workflows: {
                type: config.workflowType,
                id: 1,
                interpretation: {
                    data: {
                        alleles
                    },
                    selectedId: interpretation.id,
                    state: interpretation.state,
                    userState: interpretation.user_state,
                    isOngoing: interpretation.status === 'Ongoing'
                },
                data: {
                    interpretations: [interpretation]
                }
            }
        }
    }
}

describe('canFinalize', function() {
    it('requires configuration', function() {
        const state = createState({})
        state.app.config.user.user_config = {}
        const result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Your user group is missing valid configuration. Contact support.']
        })
    })

    it('requires ongoing interpretation', function() {
        const state = createState({})
        state.views.workflows.data.interpretations[0].status = 'Done'
        const result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Interpretation is not Ongoing']
        })
    })

    it('checks workflow status if required', function() {
        let state = createState({
            workflowStatus: 'Interpretation',
            requiredWorkflowStatus: ['Review']
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['You are not in one of the required workflow stages: Review']
        })

        state = createState({
            workflowStatus: 'Review',
            requiredWorkflowStatus: ['Review']
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })
    })

    it('can finalize when no alleles', function() {
        // No variants
        const state = createState({
            allowUnclassified: false,
            allowNotRelevant: false,
            allowTechnical: false
        })
        const result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })
    })


    it('check require classifications', function() {
        let state = createState({
            numUnclassified: 1,
            allowUnclassified: false
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants are missing classifications: TestUnclassified id 1']
        })

        state = createState({
            numUnclassified: 1,
            allowUnclassified: true
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })

        state = createState({
            numOutdated: 1,
            allowUnclassified: false
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants are missing classifications: TestOutdated id 1']
        })

        state = createState({
            numOutdated: 1,
            allowUnclassified: true
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })
    })

    it('check not submitted classifications', function() {
        let state = createState({
            numNotSubmitted: 1
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: [
                'Some variants have classifications that are not finalized: TestNotSubmitted id 1'
            ]
        })

        state = createState({
            numNotSubmittedReused: 1
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: [
                'Some variants have classifications that are not finalized: TestNotSubmittedReused id 1'
            ]
        })
    })

    it('check not submitted variant reports', function() {
        // If no existing assessment/report, no report warning should be given
        let state = createState({
            allowUnclassified: true,
            numUpdatedReportNoExisting: 1
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })

        // If there is an assessment/report already, emit warning if report has changed
        // in state, as it then hasn't been submitted
        state = createState({
            numUpdatedReport: 1
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants have reports that are not submitted: TestUpdatedReport id 1']
        })
    })

    it('check require classifications, various cases', function() {
        let state = createState({
            numUnclassified: 1,
            numClassified: 1,
            numNotRelevant: 2,
            numTechnical: 2,
            allowUnclassified: false,
            allowNotRelevant: true,
            allowTechnical: true
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants are missing classifications: TestUnclassified id 5']
        })

        state = createState({
            numTechnical: 1,
            numUnclassified: 1,
            numClassified: 3,
            numOutdated: 1,
            allowTechnical: true,
            allowUnclassified: false
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: [
                'Some variants are missing classifications: TestUnclassified id 2, TestOutdated id 6'
            ]
        })

        state = createState({
            numUnclassified: 1,
            numClassified: 1,
            numNotRelevant: 2,
            numTechnical: 2,
            allowUnclassified: true,
            allowNotRelevant: true,
            allowTechnical: true
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })

        state = createState({
            numUnclassified: 1,
            numClassified: 1,
            numNotRelevant: 2,
            numTechnical: 2,
            allowUnclassified: true,
            allowNotRelevant: false,
            allowTechnical: false
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: [
                'Some variants are marked as technical, while this is disallowed in configuration.',
                'Some variants are marked as not relevant, while this is disallowed in configuration.'
            ]
        })
    })

    it('test allele workflow case', function() {
        let state = createState({
            workflowType: 'allele',
            numUnclassified: 1
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants are missing classifications: TestUnclassified id 1']
        })

        state = createState({
            numClassified: 1
        })
        result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: true,
            messages: []
        })
    })
})
