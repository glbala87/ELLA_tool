import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (allele) => {
    return Compute(
        allele,
        state`views.workflows.data.collisions`,
        state`app.user`,
        (allele, collisions, user, get) => {
            if (!allele || !user) {
                return []
            }

            let warnings = []
            if (collisions) {
                for (const c of collisions.filter((c) => c.allele_id === allele.id)) {
                    const typeText =
                        c.type === 'analysis'
                            ? `in another analysis: ${c.analysis_name}`
                            : 'in variant workflow'
                    const unfinishedTypeText =
                        c.type === 'analysis'
                            ? `an analysis: ${c.analysis_name}`
                            : 'a variant workflow'

                    if (c.user) {
                        warnings.push({
                            warning: `This variant is currently being worked on by ${c.user.full_name} ${typeText}.`
                        })
                    } else {
                        warnings.push({
                            warning: `This variant is currently waiting in ${c.workflow_status.toUpperCase()} in ${unfinishedTypeText}.`
                        })
                    }
                }

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
            }
        }
    )
}
