import { runCompute } from 'cerebral/test'
import { state } from 'cerebral/tags'

import getConsequenceById from './getConsequenceById'

const STATE = {
    views: {
        workflows: {
            interpretation: {
                data: {
                    alleles: {
                        1: {
                            annotation: {
                                filtered: [
                                    {
                                        consequences: ['C3', 'C3', 'C3']
                                    }
                                ]
                            }
                        },
                        2: {
                            annotation: {
                                filtered: [
                                    {
                                        consequences: ['C3', 'C2', 'C1']
                                    }
                                ]
                            }
                        },
                        3: {
                            annotation: {
                                filtered: [
                                    {
                                        consequences: ['C1', 'C2', 'C4']
                                    }
                                ]
                            }
                        },
                        4: {
                            annotation: {
                                filtered: [
                                    {
                                        consequences: []
                                    }
                                ]
                            }
                        },
                        5: {
                            annotation: {
                                filtered: [
                                    {
                                        consequences: []
                                    },
                                    {
                                        consequences: ['C3', 'C4']
                                    },
                                    {
                                        consequences: ['C4', 'C2', 'C3']
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    },
    app: {
        config: {
            transcripts: {
                consequences: ['C1', 'C2', 'C3', 'C4']
            }
        }
    }
}

it('provides correct results', () => {
    const result = runCompute(
        getConsequenceById(state`views.workflows.interpretation.data.alleles`),
        {
            state: STATE
        }
    )
    expect(result).toEqual({
        // Just one when duplicates
        1: 'C3',
        // Multiple
        2: 'C1, C2, C3',
        // Multiple, different order
        3: 'C1, C2, C4',
        // None
        4: '',
        // Multiple transcripts
        5: 'C2, C3, C4'
    })
})
