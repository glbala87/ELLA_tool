import { runAction } from 'cerebral/test'

import filterAndFlattenGenepanel from './filterAndFlattenGenepanel'

describe('filterAndFlattenGenepanel', function() {
    it('filters and flattens correctly', function() {
        const testState = {
            test: {
                sourceGenepanel: {
                    genes: {
                        GENE_SHOULD_MATCH: {
                            hgnc_id: 1,
                            hgnc_symbol: 'GENE_SHOULD_MATCH test SOME MORE TEXT',
                            transcripts: [
                                {
                                    id: 1,
                                    transcript_name: 'not a match'
                                },
                                {
                                    id: 2,
                                    transcript_name: 'not a match 2'
                                }
                            ],
                            phenotypes: [
                                {
                                    id: 1,
                                    inheritance: 'AR'
                                }
                            ]
                        },
                        TRANSCRIPT_SHOULD_MATCH: {
                            hgnc_id: 2,
                            hgnc_symbol: 'TRANSCRIPT_SHOULD_MATCH',
                            transcripts: [
                                {
                                    id: 1,
                                    transcript_name: 'nametestname'
                                },
                                {
                                    id: 2,
                                    transcript_name: 'not a match'
                                }
                            ],
                            phenotypes: [
                                {
                                    id: 1,
                                    inheritance: 'AR'
                                }
                            ]
                        },
                        GENE_NO_MATCH: {
                            hgnc_id: 3,
                            hgnc_symbol: 'GENE_NO_MATCH',
                            transcripts: [
                                {
                                    id: 3,
                                    transcript_name: 'not a match'
                                }
                            ],
                            phenotypes: []
                        }
                    }
                },
                flattenedDest: null,
                query: 'test'
            }
        }
        const action = filterAndFlattenGenepanel(
            'test.sourceGenepanel',
            'test.flattenedDest',
            'test.query'
        )
        return runAction(action, { state: testState }).then(({ state }) => {
            expect(state.test.flattenedDest).toEqual([
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE_SHOULD_MATCH test SOME MORE TEXT',
                    transcript_name: 'not a match',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 1,
                    hgnc_symbol: 'GENE_SHOULD_MATCH test SOME MORE TEXT',
                    transcript_name: 'not a match 2',
                    inheritance: 'AR'
                },
                {
                    hgnc_id: 2,
                    hgnc_symbol: 'TRANSCRIPT_SHOULD_MATCH',
                    transcript_name: 'nametestname',
                    inheritance: 'AR'
                }
            ])
        })
    })
})
