import { state, props, string } from 'cerebral/tags'
import { Compute } from 'cerebral'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds,
    isIgnored
} from '../../../../../common/helpers/reference'
import getReferenceAssessment from './getReferenceAssessment'

export default function(type, allele, interpretation, references) {
    return Compute(
        type,
        allele,
        interpretation,
        references,
        (type, allele, interpretation, references, get) => {
            if (!allele || !references) {
                return null
            }
            if (!['pending', 'evaluated', 'excluded'].includes(type)) {
                throw Error(`Invalid type ${type}`)
            }
            references = Object.values(references)
            const alleleState = interpretation.state.allele[allele.id]
            const ids = getReferencesIdsForAllele(allele)
            const {
                missing: missingReferences,
                references: referencesForAllele
            } = findReferencesFromIds(references, ids)
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
                        r.published &&
                        get(getReferenceAssessment(allele.id, r.id))
                )

                result.evaluated.unpublished = referencesForAllele.filter(
                    (r) =>
                        !isIgnored(get(getReferenceAssessment(allele.id, r.id))) &&
                        !r.published &&
                        get(getReferenceAssessment(allele.id, r.id))
                )
            }

            //
            // Excluded
            //
            if (type === 'excluded') {
                result.excluded.published = referencesForAllele.filter(
                    (r) => isIgnored(get(getReferenceAssessment(allele.id, r.id))) && r.published
                )

                result.excluded.unpublished = referencesForAllele.filter(
                    (r) => isIgnored(get(getReferenceAssessment(allele.id, r.id))) && !r.published
                )
            }
            return result
        }
    )
}
