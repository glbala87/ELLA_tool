import { runCompute } from 'cerebral/test'
import { state } from 'cerebral/tags'

import getHiFrequency from './getHiFrequency'

const STATE = {
    views: {
        workflows: {
            data: {
                alleles: {
                    // With data, num constraint high enough
                    1: {
                        annotation: {
                            frequencies: {
                                FREQ_GROUP_W_CONSTRAINT: {
                                    freq: { G: 0.1 },
                                    num: { G: 5000 },
                                    count: { G: 999 }
                                },
                                NOT_PART_OF_CONFIG: {
                                    freq: { G: 1.0 },
                                    num: { G: 9999999 },
                                    count: { G: 999999 }
                                }
                            }
                        }
                    },
                    // With data, num constraint too low
                    2: {
                        annotation: {
                            frequencies: {
                                FREQ_GROUP_W_CONSTRAINT: {
                                    freq: { G: 0.1 },
                                    num: { G: 1 },
                                    count: { G: 999 }
                                },
                                NOT_PART_OF_CONFIG: {
                                    freq: { G: 1.0 },
                                    num: { G: 9999999 },
                                    count: { G: 999999 }
                                }
                            }
                        }
                    },
                    // With data, only without num constraint
                    3: {
                        annotation: {
                            frequencies: {
                                FREQ_GROUP_WO_CONSTRAINT: {
                                    freq: { G: 0.2 },
                                    num: { G: 1 },
                                    count: { G: 1000 }
                                },
                                NOT_PART_OF_CONFIG: {
                                    freq: { G: 1.0 },
                                    num: { G: 9999999 },
                                    count: { G: 999999 }
                                }
                            }
                        }
                    },
                    // With data, both w/wo num constraint
                    4: {
                        annotation: {
                            frequencies: {
                                FREQ_GROUP_W_CONSTRAINT: {
                                    freq: { G: 0.2 },
                                    num: { G: 6000 },
                                    count: { G: 1000 }
                                },
                                FREQ_GROUP_WO_CONSTRAINT: {
                                    freq: { G: 0.3 },
                                    num: { G: 1 },
                                    count: { G: 2000 }
                                },
                                NOT_PART_OF_CONFIG: {
                                    freq: { G: 1.0 },
                                    num: { G: 9999999 },
                                    count: { G: 999999 }
                                }
                            }
                        }
                    },
                    // Without data
                    5: {
                        annotation: {
                            frequencies: {
                                NOT_PART_OF_CONFIG: {
                                    freq: { G: 1.0 },
                                    num: { G: 9999999 },
                                    count: { G: 999999 }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    app: {
        config: {
            frequencies: {
                groups: {
                    external: {
                        FREQ_GROUP_W_CONSTRAINT: ['G'],
                        FREQ_GROUP_WO_CONSTRAINT: ['G']
                    }
                }
            },
            filter: {
                default_filter_config: {
                    frequency: {
                        num_thresholds: {
                            FREQ_GROUP_W_CONSTRAINT: { G: 2000 }
                        }
                    }
                }
            }
        }
    }
}

it('should give highest count regardless of num', () => {
    const result = runCompute(getHiFrequency(state`views.workflows.data.alleles`, 'count'), {
        state: STATE
    })
    expect(result).toEqual({
        1: { maxMeetsThresholdValue: 999, maxValue: 999 },
        2: { maxMeetsThresholdValue: 999, maxValue: 999 },
        3: { maxMeetsThresholdValue: 1000, maxValue: 1000 },
        4: { maxMeetsThresholdValue: 2000, maxValue: 2000 },
        5: { maxMeetsThresholdValue: null, maxValue: null }
    })
})

it('should give highest freq depending on num', () => {
    const result = runCompute(getHiFrequency(state`views.workflows.data.alleles`, 'freq'), {
        state: STATE
    })
    expect(result).toEqual({
        '1': {
            maxMeetsThresholdValue: 0.1,
            maxValue: 0.1
        },
        '2': {
            maxMeetsThresholdValue: null,
            maxValue: 0.1
        },
        '3': {
            maxMeetsThresholdValue: 0.2,
            maxValue: 0.2
        },
        '4': {
            maxMeetsThresholdValue: 0.3,
            maxValue: 0.3
        },
        '5': {
            maxMeetsThresholdValue: null,
            maxValue: null
        }
    })
})
