import { runAction } from 'cerebral/test'

import prepareInterpretationState from './prepareInterpretationState'

describe('prepareInterpretationState', function() {
    it('is initialized when state is empty', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {},
                        userState: {},
                        data: {
                            alleles: {
                                1: {}
                            }
                        }
                    }
                }
            }
        }
        return runAction(prepareInterpretationState, { state: testState }).then(({ state }) => {
            expect(state.views.workflows.interpretation.state.allele[1]).toBeDefined()
            expect(state.views.workflows.interpretation.userState.allele[1]).toBeDefined()
        })
    })
})
