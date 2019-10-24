export default function copyGenesToClipboard({ clipboard, state, props }) {
    const { includeTranscripts, genes } = props

    let formattedGenes = []
    for (let gene of genes) {
        let formattedGene = gene.hgnc_symbol
        if (includeTranscripts) {
            formattedGene += ` (${gene.transcripts.map((t) => t.transcript_name).join(',')})`
        }
        formattedGenes.push(formattedGene)
    }

    clipboard.copy(formattedGenes.join(', '))
}
