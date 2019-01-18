import canFinalize from '../computed/canFinalize'
import getSelectedInterpretation from '../computed/getSelectedInterpretation'

export default function(finishType) {
    return function finishAllowed({ resolve, state, http, path }) {
        const type = state.get('views.workflows.type')
        const id = state.get('views.workflows.id')
        const interpretation = resolve.value(getSelectedInterpretation)
        if (
            !['Not ready', 'Interpretation', 'Review', 'Medical review', 'Finalized'].includes(
                finishType
            )
        ) {
            console.error(`Invalid finishType ${finishType}`)
            return path.false({ errorMessage: `Invalid finishType ${finishType}` })
        }

        if (interpretation.status !== 'Ongoing') {
            console.error('Trying to mark review when interpretation status is not Ongoing')
            return path.false({
                errorMessage: 'Trying to mark review when interpretation status is not Ongoing'
            })
        }

        if (finishType === 'Finalized') {
            const finalizeAllowed = resolve.value(canFinalize).canFinalize
            if (!finalizeAllowed) {
                console.error('Tried to finalize workflow when requirements not met')
                return path.false({
                    errorMessage: 'Tried to finalize workflow when requirements not met'
                })
            }
        }

        if (type === 'analysis') {
            const sampleIds = state.get(`views.workflows.data.analysis.samples`).map((s) => s.id)
            let rest_filter = encodeURIComponent(JSON.stringify({ sample_ids: sampleIds }))
            return http
                .get(
                    `workflows/analyses/${id}/interpretations/${
                        interpretation.id
                    }/finishallowed?q=${rest_filter}`
                )
                .then((r) => {
                    return path.true()
                })
                .catch((r) => {
                    console.error(r.response.result)
                    return path.false({ errorMessage: r.response.result })
                })
        } else {
            return path.true()
        }
    }
}
