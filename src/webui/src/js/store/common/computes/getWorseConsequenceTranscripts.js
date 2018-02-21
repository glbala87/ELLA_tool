import { state, props, string } from 'cerebral/tags'
import { Compute } from 'cerebral'

/**
 * Returns transcripts with consequences worse that the filtered transcripts.
 * If all worst transcripts are in filtered, an empty list is returned
 */
export default function(allele) {
    return Compute(allele, allele => {
        if (!allele) {
            return []
        }
        return allele.annotation.worst_consequence
            .filter(t => {
                return !allele.annotation.filtered_transcripts.includes(t)
            })
            .map(name => {
                return allele.annotation.transcripts.find(t => t.transcript === name)
            })
    })
}
