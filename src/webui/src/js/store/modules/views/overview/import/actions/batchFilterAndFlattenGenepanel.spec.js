import { runAction } from 'cerebral/test'

import batchFilterAndFlattenGenepanel from './batchFilterAndFlattenGenepanel'

function getState() {
    return {
        views: {
            overview: {
                import: {
                    data: {
                        genepanel: {
                            genes: {
                                GENE1: {
                                    hgnc_id: 1,
                                    hgnc_symbol: 'GENE1',
                                    transcripts: [
                                        {
                                            id: 1,
                                            transcript_name: 'T1'
                                        },
                                        {
                                            id: 2,
                                            transcript_name: 'T2'
                                        }
                                    ],
                                    phenotypes: [
                                        {
                                            id: 1,
                                            inheritance: 'AR'
                                        }
                                    ]
                                },
                                GENE2: {
                                    hgnc_id: 2,
                                    hgnc_symbol: 'GENE2',
                                    transcripts: [
                                        {
                                            id: 1,
                                            transcript_name: 'T1'
                                        },
                                        {
                                            id: 2,
                                            transcript_name: 'T2'
                                        }
                                    ],
                                    phenotypes: [
                                        {
                                            id: 1,
                                            inheritance: 'AR'
                                        }
                                    ]
                                },
                                GENE3: {
                                    hgnc_id: 3,
                                    hgnc_symbol: 'GENE3',
                                    transcripts: [
                                        {
                                            id: 1,
                                            transcript_name: 'T1'
                                        }
                                    ],
                                    phenotypes: []
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

describe('batchFilterAndFlattenGenepanel', function() {
    it('all matches: symbols', function() {
        const state = getState()
        state.views.overview.import.custom = {
            candidates: {
                filterBatch: 'GENE1,GENE2; GENE3'
            }
        }
        return runAction(batchFilterAndFlattenGenepanel, { state }).then(({ state }) => {
            expect(state.views.overview.import.custom.candidates.filterBatchProcessed).toBe(true)
            expect(state.views.overview.import.custom.candidates.filterBatch).toEqual('')
            expect(state.views.overview.import.custom.candidates.missingBatch).toEqual([])
            expect(state.views.overview.import.custom.candidates.filteredFlattened).toEqual([
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'GENE2',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'GENE2',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 3,
                    hgnc_symbol: 'GENE3',
                    transcript_name: 'T1',
                    inheritance: ''
                }
            ])
        })
    })

    it('all matches: mix', function() {
        const state = getState()
        state.views.overview.import.custom = {
            candidates: {
                filterBatch: 'GENE1,2\n3'
            }
        }
        return runAction(batchFilterAndFlattenGenepanel, { state }).then(({ state }) => {
            expect(state.views.overview.import.custom.candidates.filterBatchProcessed).toBe(true)
            expect(state.views.overview.import.custom.candidates.filterBatch).toEqual('')
            expect(state.views.overview.import.custom.candidates.missingBatch).toEqual([])
            expect(state.views.overview.import.custom.candidates.filteredFlattened).toEqual([
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'GENE2',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'GENE2',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 3,
                    hgnc_symbol: 'GENE3',
                    transcript_name: 'T1',
                    inheritance: ''
                }
            ])
        })
    })

    it('missing', function() {
        const state = getState()
        state.views.overview.import.custom = {
            candidates: {
                filterBatch: 'GENE1,GENE2,GENENOTHERE; someothergene, 488484'
            }
        }
        return runAction(batchFilterAndFlattenGenepanel, { state }).then(({ state }) => {
            expect(state.views.overview.import.custom.candidates.filterBatchProcessed).toBe(true)
            expect(state.views.overview.import.custom.candidates.filterBatch).toEqual(
                'GENENOTHERE\nsomeothergene\n488484'
            )
            expect(state.views.overview.import.custom.candidates.missingBatch).toEqual([
                'GENENOTHERE',
                'someothergene',
                '488484'
            ])
            expect(state.views.overview.import.custom.candidates.filteredFlattened).toEqual([
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'GENE2',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'GENE2',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                }
            ])
        })
    })

    it('cleans up bad input', function() {
        const state = getState()
        state.views.overview.import.custom = {
            candidates: {
                filterBatch: ';,GENE1,;\n  \n; GENENOTFOUND ,'
            }
        }
        return runAction(batchFilterAndFlattenGenepanel, { state }).then(({ state }) => {
            expect(state.views.overview.import.custom.candidates.filterBatchProcessed).toBe(true)
            expect(state.views.overview.import.custom.candidates.filterBatch).toEqual(
                'GENENOTFOUND'
            )
            expect(state.views.overview.import.custom.candidates.missingBatch).toEqual([
                'GENENOTFOUND'
            ])
            expect(state.views.overview.import.custom.candidates.filteredFlattened).toEqual([
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T1',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE1',
                    transcript_name: 'T2',
                    inheritance: 'AR'
                }
            ])
        })
    })
})
