import { runCompute } from 'cerebral/test'

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
                view: {
                    precision: 2,
                    scientific_threshold: 1000
                }
            },
            variant_criteria: {
                freq_num_thresholds: {
                    FREQ_GROUP_W_CONSTRAINT: { G: 2000 }
                },
                frequencies: {
                    groups: {
                        external: {
                            FREQ_GROUP_W_CONSTRAINT: ['G'],
                            FREQ_GROUP_WO_CONSTRAINT: ['G']
                        }
                    }
                }
            }
        }
    }
}

it('should give highest count regardless of num', () => {
    const result = runCompute(getHiFrequency('count'), {
        state: STATE
    })
    console.log(result)
    expect(result).toEqual({ 1: 999, 2: 999, 3: 1000, 4: 2000, 5: null })
})

it('should give highest freq depending on num', () => {
    const result = runCompute(getHiFrequency('freq'), {
        state: STATE
    })
    expect(result).toEqual({ 1: '0.10', 2: null, 3: '0.20', 4: '0.30', 5: null })
})
