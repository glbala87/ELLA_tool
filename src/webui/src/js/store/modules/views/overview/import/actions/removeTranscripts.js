export default function removeTranscripts({ state, props }) {
    const addedGenepanel = state.get('views.overview.import.custom.added.addedGenepanel')
    let { removed: toRemove } = props
    if (!Array.isArray(toRemove)) {
        toRemove = [toRemove]
    }

    for (const t of toRemove) {
        if (t.hgnc_id in addedGenepanel.genes) {
            addedGenepanel.genes[t.hgnc_id].transcripts = addedGenepanel.genes[
                t.hgnc_id
            ].transcripts.filter((at) => at.name !== t.name)
            if (!addedGenepanel.genes[t.hgnc_id].transcripts.length) {
                delete addedGenepanel.genes[t.hgnc_id]
            }
        }
    }
    state.set('views.overview.import.custom.added.addedGenepanel', addedGenepanel)
}
