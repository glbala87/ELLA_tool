import { runAction } from 'cerebral/test'

import addAcmgCode from './addAcmgCode'

describe('addAcmgCode', function() {
    it('inserts code correctly', async function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: {
                                        evaluation: {
                                            acmg: {
                                                included: []
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        const props = {
            alleleId: 1,
            code: {
                code: 'BS1',
                source: 'user'
            }
        }
        const { state } = await runAction(addAcmgCode, { state: testState, props })
        const included =
            state.views.workflows.interpretation.state.allele[1].alleleassessment.evaluation.acmg
                .included

        expect(included[0].uuid.length).toEqual(36)
        delete included[0].uuid
        expect(included).toEqual([
            {
                code: 'BS1',
                source: 'user',
                match: null,
                op: null,
                comment: ''
            }
        ])
    })

    it('does not allow duplicates', async function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: {
                                        evaluation: {
                                            acmg: {
                                                included: []
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        const props = {
            alleleId: 1,
            code: {
                code: 'BS1',
                source: 'user'
            }
        }
        await runAction(addAcmgCode, { state: testState, props })
        // Insert again, same code
        expect(runAction(addAcmgCode, { state: testState, props })).rejects.toThrow(
            'Code (or base of) BS1 is already added'
        )

        // Insert again, different code, same base
        props.code.code = 'BPxBS1'
        expect(runAction(addAcmgCode, { state: testState, props })).rejects.toThrow(
            'Code (or base of) BPxBS1 is already added'
        )
    })
})
