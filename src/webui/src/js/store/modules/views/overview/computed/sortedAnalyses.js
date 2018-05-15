import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default function sortedAnalyses(analyses) {
    return Compute(analyses, (analyses) => {
        if (analyses) {
            analyses = analyses.slice()
            analyses.sort(firstBy((a) => a.priority, -1).thenBy((a) => a.deposit_date))
            return analyses
        }
        return []
    })
}
