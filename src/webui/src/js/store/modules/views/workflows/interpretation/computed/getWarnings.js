import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (allele) => {
    return Compute(allele, state`app.user`, (allele, user) => {
        if (!allele || !user) {
            return []
        }

        let warnings = []
        if (allele.warnings) {
            warnings = warnings.concat(
                Object.values(allele.warnings).map((w) => {
                    return { warning: w }
                })
            )
        }

        if (
            allele.allele_assessment &&
            user.group.name != allele.allele_assessment.usergroup.name
        ) {
            warnings.push({
                warning: `This variant's existing classification was performed by a different user group: ${allele.allele_assessment.usergroup.name}.`
            })
        }
        return warnings
    })
}
