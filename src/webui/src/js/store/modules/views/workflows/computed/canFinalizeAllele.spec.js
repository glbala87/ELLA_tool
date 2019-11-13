import { runCompute } from 'cerebral/test'

import canFinalizeAllele from './canFinalizeAllele'

const defaultConfig = {
    workflowType: 'analysis',
    workflowStatus: 'Review',
    status: 'Ongoing',
    requiredWorkflowStatus: ['Review'],
    hasClassification: true
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

    const alleleId = 1
    if (config.hasClassification) {
        interpretation.state.allele[alleleId] = {
            alleleassessment: {
                classification: '1'
            }
        }
        alleles[alleleId] = {
            id: alleleId
        }
    } else {
        interpretation.state.allele[alleleId] = {
            alleleassessment: {}
        }
        alleles[alleleId] = {
            id: alleleId
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
                                    workflow_status: config.requiredWorkflowStatus
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

describe('canFinalizeAllele', function() {
    it('requires configuration', function() {
        const state = createState({})
        state.app.config.user.user_config = {}
        const result = runCompute(canFinalizeAllele(1), {
            state,
            props: {}
        })
        expect(result).toEqual(false)
    })

    it('requires ongoing interpretation', function() {
        const state = createState({})
        state.views.workflows.data.interpretations[0].status = 'Done'
        const result = runCompute(canFinalizeAllele(1), {
            state,
            props: {}
        })
        expect(result).toEqual(false)
    })

    it('checks workflow status if required', function() {
        let state = createState({
            workflowStatus: 'Interpretation',
            requiredWorkflowStatus: ['Review']
        })
        let result = runCompute(canFinalizeAllele(1), {
            state,
            props: {}
        })
        expect(result).toEqual(false)
    })

    it('checks classification', function() {
        let state = createState({
            workflowStatus: 'Review',
            requiredWorkflowStatus: ['Review'],
            hasClassification: false
        })
        let result = runCompute(canFinalizeAllele(1), {
            state,
            props: {}
        })
        expect(result).toEqual(false)

        state = createState({
            workflowStatus: 'Review',
            requiredWorkflowStatus: ['Review'],
            hasClassification: true
        })
        result = runCompute(canFinalizeAllele(1), {
            state,
            props: {}
        })
        expect(result).toEqual(true)
    })
})
