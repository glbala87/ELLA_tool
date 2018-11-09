import { runCompute } from 'cerebral/test'

import canFinalize from './canFinalize'

const defaultConfig = {
    workflowType: 'analysis',
    workflowStatus: 'Review',
    status: 'Ongoing',
    requiredWorkflowStatus: ['Review'],
    allowTechnical: false,
    allowNotRelevant: false,
    allowUnclassified: false,
    numTechnical: 0,
    numNotRelevant: 0,
    numUnclassified: 0,
    numClassified: 0
}

function createState(config) {
    config = Object.assign({}, defaultConfig, config)

    const interpretation = {
        id: 1,
        type: config.workflowType,
        status: config.status,
        workflow_status: config.workflowStatus,
        state: { allele: {} }
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
                classification: 1
            }
        }
        alleles[currentAlleleId] = {
            id: currentAlleleId,
            formatted: { display: `TestClassified id ${currentAlleleId}` }
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
                                    allow_technical: config.allowTechnical,
                                    allow_notrelevant: config.allowNotRelevant,
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
                }
            }
        },
        views: {
            workflows: {
                type: config.workflowType,
                id: 1,
                interpretation: {
                    selected: interpretation
                },
                data: {
                    alleles
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
        state.views.workflows.interpretation.selected.status = 'Done'
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

    it('check allow_technical', function() {
        let state = createState({
            numTechnical: 1,
            allowTechnical: false
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants are missing classifications: TestTechnical id 1']
        })

        state = createState({
            numTechnical: 1,
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
    })

    it('check allow_notrelevant', function() {
        let state = createState({
            numNotRelevant: 1,
            allowNotRelevant: false
        })
        let result = runCompute(canFinalize, {
            state,
            props: {}
        })
        expect(result).toEqual({
            canFinalize: false,
            messages: ['Some variants are missing classifications: TestNotRelevant id 1']
        })

        state = createState({
            numNotRelevant: 1,
            allowNotRelevant: true
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
