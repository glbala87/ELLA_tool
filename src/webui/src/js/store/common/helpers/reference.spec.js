import { getReferencesIdsForAllele, findReferencesFromIds } from './reference'

const BASEALLELE = {
    annotation: {
        references: []
    },
    reference_assessments: []
}

describe('merges reference assessments references with annotation references', function() {
    it('reference only in annotation', function() {
        let references = [
            {
                pubmed_id: 1000000,
                id: 1
            }
        ]
        let allele = {
            annotation: {
                references: [{ pubmed_id: 1000000 }]
            },
            reference_assessments: []
        }

        let ids = getReferencesIdsForAllele(allele)

        let referencesFromIds = findReferencesFromIds(references, ids)

        expect(referencesFromIds.references).toEqual(references)
        expect(ids.length).toEqual(1)
    })

    it('reference only in reference assessment', function() {
        let references = [
            {
                pubmed_id: 1000000,
                id: 1
            }
        ]
        let allele = {
            annotation: {
                references: []
            },
            reference_assessments: [{ reference_id: 1 }]
        }

        let ids = getReferencesIdsForAllele(allele)

        let referencesFromIds = findReferencesFromIds(references, ids)

        expect(referencesFromIds.references).toEqual(references)
        expect(ids.length).toEqual(1)
    })

    it('same reference in annotation and reference assessments', function() {
        let references = [
            {
                pubmed_id: 1000000,
                id: 1
            }
        ]

        let allele = {
            annotation: {
                references: [{ pubmed_id: 1000000 }]
            },
            reference_assessments: [{ reference_id: 1 }]
        }

        let ids = getReferencesIdsForAllele(allele)

        let referencesFromIds = findReferencesFromIds(references, ids)

        expect(referencesFromIds.references).toEqual(references)
        expect(ids.length).toEqual(2)
    })
})
