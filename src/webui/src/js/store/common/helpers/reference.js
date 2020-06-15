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

    // References migth drop from annotation, even though a reference assessment is already performed.
    // Make sure these references are added to allele references
    if (allele.reference_assessments) {
        for (let ra of allele.reference_assessments) {
            ids.push({
                id: ra.reference_id
            })
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
            let reference = references.find((r) => {
                return (
                    (pmid && r.pubmed_id && r.pubmed_id.toString() === pmid.toString()) ||
                    (id && r.id === id)
                )
            })
            // Avoid duplicated references in result
            if (result.references.includes(reference)) {
                continue
            }
            if (reference) {
                result.references.push(reference)
            } else {
                result.missing.push(rid)
            }
        }
    }
    return result
}

export function isIgnored(referenceAssessment) {
    if (referenceAssessment && referenceAssessment.evaluation) {
        return referenceAssessment.evaluation.relevance === 'Ignore'
    }
    return false
}

export function isNotRelevant(referenceAssessment) {
    if (referenceAssessment && referenceAssessment.evaluation) {
        return referenceAssessment.evaluation.relevance === 'No'
    }
    return false
}
