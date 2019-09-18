import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import { isIgnored } from '../../../../../common/helpers/reference.js'

export default (alleles) => {
    return Compute(
        alleles,
        state`views.workflows.interpretation.state.allele`,
        (alleles, alleleStates) => {
            if (!alleles || !alleleStates) {
                return {}
            }

            const result = {}
            for (let [alleleId, allele] of Object.entries(alleles)) {
                let totalRefs = 'references' in allele.annotation ? allele.annotation.references.length : 0
                let ignoredRefs = 0
                if (totalRefs > 0) {
                    if (
                        Object.keys(alleleStates).includes(alleleId) &&
                        'referenceassessments' in alleleStates[alleleId] &&
                        alleleStates[alleleId].referenceassessments
                    ) {
                        ignoredRefs = alleleStates[
                            alleleId
                        ].referenceassessments.filter(
                            (ra) => isIgnored(ra)
                        ).length
                    }
                }
                result[alleleId] = totalRefs - ignoredRefs > 0
            }
            return result
        }
    )
}
