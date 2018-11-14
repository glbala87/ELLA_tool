import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default function sortedAnalyses(analyses) {
    return Compute(analyses, (analyses) => {
        if (analyses) {
            analyses = analyses.slice()
            analyses.sort(
                thenBy((a) => a.priority, -1).thenBy((a) => a.date_requested || a.date_deposited)
            )
            return analyses
        }
        return []
    })
}
