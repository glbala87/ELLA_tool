export default function addTranscripts({ state, props }) {
    const sourceGenepanel = state.get('views.overview.import.data.genepanel')
    const addedGenepanel = state.get('views.overview.import.custom.added.addedGenepanel')
    let { added: toAdd } = props
    // Find already added ones
    if (!Array.isArray(toAdd)) {
        toAdd = [toAdd]
    }
    for (const item of toAdd) {
        if (
            // Gene not added or transcript not added
            !(item.hgnc_id in addedGenepanel.genes) ||
            !Boolean(
                addedGenepanel.genes[item.hgnc_id].transcripts.find(
                    (t) => t.transcript_name === item.transcript_name
                )
            )
        ) {
            // Add transcript and merge in phenotypes and config from selected panel
            const sourceGene = sourceGenepanel.genes[item.hgnc_id]
            const sourceTranscript = sourceGene.transcripts.find(
                (t) => t.transcript_name === item.transcript_name
            )
            if (!sourceTranscript) {
                throw Error(`Couldn't find transcript ${item.transcript_name} in source genepanel.`)
            }
            if (!(item.hgnc_id in addedGenepanel.genes)) {
                addedGenepanel.genes[item.hgnc_id] = {
                    hgnc_id: sourceGene.hgnc_id,
                    hgnc_symbol: sourceGene.hgnc_symbol,
                    transcripts: [],
                    phenotypes: []
                }
            }
            addedGenepanel.genes[item.hgnc_id].transcripts.push(sourceTranscript)
            addedGenepanel.genes[item.hgnc_id].phenotypes = addedGenepanel.genes[
                item.hgnc_id
            ].phenotypes.concat(
                sourceGene.phenotypes.filter((p) => {
                    return !addedGenepanel.genes[item.hgnc_id].phenotypes.find((sp) => {
                        return sp.id === p.id
                    })
                })
            )
        }
    }

    state.set('views.overview.import.custom.added.addedGenepanel', addedGenepanel)
}
