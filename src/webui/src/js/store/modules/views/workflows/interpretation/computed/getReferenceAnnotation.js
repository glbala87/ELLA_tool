import thenBy from 'thenby'
import { Compute } from 'cerebral'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds,
    isIgnored,
    isNotRelevant
} from '../../../../../common/helpers/reference'
import getReferenceAssessment from './getReferenceAssessment'

export default function(type, allele, references) {
    return Compute(type, allele, references, (type, allele, references, get) => {
        if (!allele || !references) {
            return null
        }

        if (!['pending', 'evaluated', 'ignored', 'notrelevant'].includes(type)) {
            throw Error(`Invalid type ${type}`)
        }
        references = Object.values(references)
        const ids = getReferencesIdsForAllele(allele)
        let { missing: missingReferences, references: referencesForAllele } = findReferencesFromIds(
            references,
            ids
        )
        referencesForAllele = referencesForAllele.sort(
            thenBy((x) => x.year || 0, -1).thenBy((x) => x.authors)
        )
        const result = {}

        Object.assign(result, {
            [type]: {
                published: [],
                unpublished: []
            }
        })
        if (type === 'pending') {
            result.missing = missingReferences
        }

        //
        // Pending
        //
        if (type === 'pending') {
            result.pending.published = referencesForAllele.filter(
                (r) => r.published && !get(getReferenceAssessment(allele.id, r.id))
            )

            result.pending.unpublished = referencesForAllele.filter(
                (r) => !r.published && !get(getReferenceAssessment(allele.id, r.id))
            )
        }

        //
        // Evaluated
        //
        if (type === 'evaluated') {
            result.evaluated.published = referencesForAllele.filter(
                (r) =>
                    !isIgnored(get(getReferenceAssessment(allele.id, r.id))) &&
                    !isNotRelevant(get(getReferenceAssessment(allele.id, r.id))) &&
                    r.published &&
                    get(getReferenceAssessment(allele.id, r.id))
            )

            result.evaluated.unpublished = referencesForAllele.filter(
                (r) =>
                    !isIgnored(get(getReferenceAssessment(allele.id, r.id))) &&
                    !isNotRelevant(get(getReferenceAssessment(allele.id, r.id))) &&
                    !r.published &&
                    get(getReferenceAssessment(allele.id, r.id))
            )
        }

        //
        // Not relevant
        //
        if (type === 'notrelevant') {
            result.notrelevant.published = referencesForAllele.filter(
                (r) => isNotRelevant(get(getReferenceAssessment(allele.id, r.id))) && r.published
            )

            result.notrelevant.unpublished = referencesForAllele.filter(
                (r) => isNotRelevant(get(getReferenceAssessment(allele.id, r.id))) && !r.published
            )
        }

        //
        // Ignored
        //
        if (type === 'ignored') {
            result.ignored.published = referencesForAllele.filter(
                (r) => isIgnored(get(getReferenceAssessment(allele.id, r.id))) && r.published
            )

            result.ignored.unpublished = referencesForAllele.filter(
                (r) => isIgnored(get(getReferenceAssessment(allele.id, r.id))) && !r.published
            )
        }
        return result
    })
}
