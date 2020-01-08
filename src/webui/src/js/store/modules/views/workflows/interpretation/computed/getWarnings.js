import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (allele) => {
    return Compute(allele, state`views.workflows.data.collisions`, (allele, collisions, get) => {
        if (!allele) {
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
                        ? `an unfinished analysis: ${c.analysis_name}`
                        : 'an unfinished variant workflow'

                if (c.user) {
                    warnings.push({
                        warning: `This variant is currently being worked on by ${c.user.full_name} ${typeText}.`
                    })
                } else {
                    warnings.push({
                        warning: `This variant is currently waiting in ${unfinishedTypeText}.`
                    })
                }
            }
        }

        if (allele.warnings) {
            warnings = warnings.concat(
                Object.values(allele.warnings).map((w) => {
                    return { warning: w }
                })
            )
        }
        return warnings
    })
}
