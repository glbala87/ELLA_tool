import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'

export default Compute(
    state`views.workflows.type`,
    state`views.workflows.data.analysis`,
    state`views.workflows.interpretation.data.alleles`,
    state`views.workflows.data.interpretations`,
    (workflowType, analysis, alleles, interpretations) => {
        let title = ''
        if (!workflowType) {
            return title
        }
        if (workflowType === 'analysis') {
            title += analysis.name
        } else if (workflowType === 'allele') {
            if (alleles) {
                title += Object.values(alleles)[0].formatted.display
            }
        }
        if (interpretations && interpretations.length) {
            const lastInterpretation = interpretations[interpretations.length - 1]
            const workflowStatus = lastInterpretation.workflow_status.toUpperCase()
            title += ` • ${workflowStatus}`
        }

        return title
    }
)
