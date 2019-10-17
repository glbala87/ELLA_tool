import { runAction } from 'cerebral/test'

import autoIgnoreReferences from './autoIgnoreReferences'

describe('autoIgnoreReferences', function() {
    it('ignore references if in ignore list and no previous assessment', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: {},
                                    referenceassessments: []
                                }
                            }
                        },
                        data: {
                            alleles: {
                                1: {
                                    reference_assessments: [],
                                    annotation: {
                                        references: [
                                            {
                                                pubmed_id: 1234567890
                                            },

                                            {
                                                pubmed_id: 9876543210
                                            }
                                        ]
                                    }
                                }
                            },
                            references: {
                                1: {
                                    id: 1,
                                    allele_id: 1,
                                    pubmed_id: 1234567890
                                },
                                2: {
                                    id: 2,
                                    allele_id: 1,
                                    pubmed_id: 9876543210
                                }
                            }
                        }
                    }
                }
            },
            app: {
                config: {
                    user: {
                        user_config: {
                            interpretation: {
                                autoIgnoreReferencePubmedIds: [1234567890]
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoIgnoreReferences, { state: testState }).then(({ state }) => {
            expect(
                state.views.workflows.interpretation.state.allele[1].referenceassessments
            ).toEqual([
                {
                    reference_id: 1,
                    allele_id: 1,
                    evaluation: {
                        relevance: 'Ignore',
                        comment: 'Automatically ignored according to user group configuration'
                    }
                }
            ])

            expect(
                state.views.workflows.interpretation.data.alleles['1'].annotation.references.length
            ).toEqual(2)
        })
    })

    it('do not ignore any if autoIgnoreReferencePubmedIds is empty', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: {},
                                    referenceassessments: []
                                }
                            }
                        },
                        data: {
                            alleles: {
                                1: {
                                    reference_assessments: [],
                                    annotation: {
                                        references: [
                                            {
                                                pubmed_id: 1234567890
                                            },
                                            {
                                                pubmed_id: 9876543210
                                            }
                                        ]
                                    }
                                }
                            },
                            references: {
                                1: {
                                    id: 1,
                                    allele_id: 1,
                                    pubmed_id: 1234567890
                                },
                                2: {
                                    id: 2,
                                    allele_id: 1,
                                    pubmed_id: 9876543210
                                }
                            }
                        }
                    }
                }
            },
            app: {
                config: {
                    user: {
                        user_config: {
                            interpretation: {
                                autoIgnoreReferencePubmedIds: []
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoIgnoreReferences, { state: testState }).then(({ state }) => {
            expect(
                state.views.workflows.interpretation.state.allele[1].referenceassessments
            ).toEqual([])

            expect(
                state.views.workflows.interpretation.data.alleles['1'].annotation.references.length
            ).toEqual(2)
        })
    })

    it('do not ignore if existing referenceassessment', function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: {},
                                    referenceassessments: [
                                        {
                                            allele_id: 1,
                                            reference_id: 1,
                                            evaluation: {
                                                relevance: 'Yes',
                                                comment: 'Keep old evaluation'
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        data: {
                            alleles: {
                                1: {
                                    reference_assessments: [],
                                    annotation: {
                                        references: [
                                            {
                                                pubmed_id: 1234567890
                                            },
                                            {
                                                pubmed_id: 9876543210
                                            }
                                        ]
                                    }
                                }
                            },
                            references: {
                                1: {
                                    id: 1,
                                    allele_id: 1,
                                    pubmed_id: 1234567890
                                },
                                2: {
                                    id: 2,
                                    allele_id: 1,
                                    pubmed_id: 9876543210
                                }
                            }
                        }
                    }
                }
            },
            app: {
                config: {
                    user: {
                        user_config: {
                            interpretation: {
                                autoIgnoreReferencePubmedIds: [1234567890]
                            }
                        }
                    }
                }
            }
        }

        return runAction(autoIgnoreReferences, { state: testState }).then(({ state }) => {
            expect(
                state.views.workflows.interpretation.state.allele[1].referenceassessments
            ).toEqual([
                {
                    allele_id: 1,
                    reference_id: 1,
                    evaluation: {
                        relevance: 'Yes',
                        comment: 'Keep old evaluation'
                    }
                }
            ])

            expect(
                state.views.workflows.interpretation.data.alleles['1'].annotation.references.length
            ).toEqual(2)
        })
    })
})
