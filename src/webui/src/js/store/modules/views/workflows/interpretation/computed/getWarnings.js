import { Compute } from 'cerebral'
import getVerificationStatus from './getVerificationStatus'
import getNotRelevant from './getNotRelevant'
import getClassification from './getClassification'

export default (allele) => {
    return Compute(allele, (allele, get) => {
        if (!allele) {
            return []
        }

        const warnings = []
        const verificationStatus = get(getVerificationStatus(allele.id))
        const notRelevant = get(getNotRelevant(allele.id))
        const classification = get(getClassification(allele))
        // If not relevant or technical, and new classification
        // give a warning
        if (
            (notRelevant || verificationStatus === 'technical') &&
            ((classification.existing && !classification.reused) ||
                (classification.current && !classification.existing))
        ) {
            let markedAs = ''
            if (notRelevant) {
                markedAs = "'Not relevant'"
            }
            if (verificationStatus === 'technical') {
                markedAs = "'Technical'"
            }
            const undoAction = classification.reused
                ? `select 'UNDO REEVALUATION' `
                : `choose 'SELECT CLASS' from the dropdown instead of an actual class`
            const updatedText = classification.reused ? 'updated' : 'created'
            warnings.push({
                warning: `Variant is marked ${markedAs}, yet it's classification is set to be ${updatedText}. To prevent this, ${undoAction}.`
            })
        }
        if (allele.warnings) {
            warnings = warnings.concat(
                Object.values(allele.warnings).map((w) => {
                    warning: w
                })
            )
        }
        return warnings
    })
}
