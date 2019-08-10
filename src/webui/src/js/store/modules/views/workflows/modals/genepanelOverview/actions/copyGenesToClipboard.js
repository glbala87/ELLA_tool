export default function copyGenesToClipboard({ clipboard, state, props }) {
    const { includeTranscripts } = props

    const genepanel = state.get('views.workflows.modals.genepanelOverview.data.genepanel')

    let formattedGenes = []
    for (let gene of genepanel.genes) {
        let formattedGene = gene.hgnc_symbol
        if (includeTranscripts) {
            formattedGene += ` (${gene.transcripts.map((t) => t.transcript_name).join(',')})`
        }
        formattedGenes.push(formattedGene)
    }

    clipboard.copy(formattedGenes.join(', '))
}
