import Annotation from './annotation'

describe('Annotation model', function() {
    // Mock data
    function getData() {
        return {
            annotation_id: 37,
            filtered_transcripts: ['NM_000123.1'],
            transcripts: [
                {
                    symbol: 'GENE1',
                    transcript: 'NM_000123.1'
                },
                {
                    symbol: 'GENE2',
                    transcript: 'NM_000321.1'
                }
            ],
            worst_consequence: ['NM_000321.1']
        }
    }

    it('can be constructed', function() {
        expect(new Annotation(getData())).toBeDefined()
    })

    it('sets filtered transcripts ', function() {
        let annotation = new Annotation(getData())
        expect(annotation.filtered).toEqual([
            {
                symbol: 'GENE1',
                transcript: 'NM_000123.1'
            }
        ])
    })

    it('reports correctly whether it has worse consequence', function() {
        let annotation = new Annotation(getData())
        expect(annotation.hasWorseConsequence()).toBeTruthy()
    })

    it('correctly returns worst consequence transcript', function() {
        let annotation = new Annotation(getData())
        expect(annotation.getWorseConsequenceTranscripts()).toEqual([
            {
                symbol: 'GENE2',
                transcript: 'NM_000321.1'
            }
        ])
    })
})
