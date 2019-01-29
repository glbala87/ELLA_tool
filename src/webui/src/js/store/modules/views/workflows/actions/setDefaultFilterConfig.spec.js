import { runAction } from 'cerebral/test'

import setDefaultFilterConfig from './setDefaultFilterConfig'

describe('setDefaultFilterConfig', function() {
    it('leaves selectedFilterConfigId alone when present', async function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            filterconfigId: 2
                        },
                        selectedId: 1
                    },
                    data: {
                        interpretations: [{ id: 1, status: 'Ongoing' }],
                        filterconfigs: [
                            {
                                id: 1
                            },
                            {
                                id: 2
                            },
                            {
                                id: 3
                            }
                        ]
                    }
                }
            }
        }

        const { state } = await runAction(setDefaultFilterConfig, { state: testState })
        expect(state.views.workflows.interpretation.state.filterconfigId).toEqual(2)
    })

    it('sets new selectedFilterConfigId when not present in available', async function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            filterconfigId: 5
                        },
                        selectedId: 1
                    },
                    data: {
                        interpretations: [{ id: 1, status: 'Ongoing' }],
                        filterconfigs: [
                            {
                                id: 1
                            },
                            {
                                id: 2
                            },
                            {
                                id: 3
                            }
                        ]
                    }
                }
            }
        }

        const { state } = await runAction(setDefaultFilterConfig, { state: testState })
        expect(state.views.workflows.interpretation.state.filterconfigId).toEqual(1)
    })

    it('uses existing selectedFilterConfigId when viewing "Done" interpretation', async function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            filterconfigId: 5
                        },
                        selectedId: 1
                    },
                    data: {
                        interpretations: [{ id: 1, status: 'Done' }],
                        filterconfigs: [
                            {
                                id: 1
                            },
                            {
                                id: 2
                            },
                            {
                                id: 3
                            }
                        ]
                    }
                }
            }
        }

        const { state } = await runAction(setDefaultFilterConfig, { state: testState })
        expect(state.views.workflows.interpretation.state.filterconfigId).toEqual(5)
    })

    it('sets new selectedFilterConfigId when viewing "current" interpretation', async function() {
        const testState = {
            views: {
                workflows: {
                    interpretation: {
                        state: {
                            filterconfigId: 1
                        },
                        selectedId: 'current'
                    },
                    data: {
                        interpretations: [{ id: 1, status: 'Done' }],
                        filterconfigs: [
                            {
                                id: 1
                            },
                            {
                                id: 2
                            },
                            {
                                id: 3
                            }
                        ]
                    }
                }
            }
        }

        const { state } = await runAction(setDefaultFilterConfig, { state: testState })
        expect(state.views.workflows.interpretation.state.filterconfigId).toEqual(1)
    })
})
