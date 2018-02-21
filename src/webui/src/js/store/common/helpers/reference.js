/* jshint esnext: true */

export function getReferencesIdsForAllele(allele) {
    const ids = []
    if (allele.annotation) {
        for (let ref of allele.annotation.references) {
            let obj = {}
            if (ref.id) {
                obj.id = ref.id
            }
            if (ref.pubmed_id) {
                obj.pubmed_id = ref.pubmed_id
            }
            ids.push(obj)
        }
    }
    return ids
}

export function findReferencesFromIds(references, ids) {
    const result = {
        references: [],
        missing: []
    }

    for (let rid of ids) {
        let pmid = rid.pubmed_id
        let id = rid.id

        if (references) {
            let reference = references.find(r => {
                return (pmid && r.pubmed_id.toString() === pmid.toString()) || (id && r.id === id)
            })
            if (reference) {
                result.references.push(reference)
            } else {
                result.missing.push(rid)
            }
        }
    }
    return result
}
