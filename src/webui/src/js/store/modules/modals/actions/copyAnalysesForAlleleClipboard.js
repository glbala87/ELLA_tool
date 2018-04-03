export default function copyAnalysesForAlleleClipboard({ state, clipboard }) {
    const allele = state.get('modals.showAnalysesForAllele.allele')
    const analyses = state.get('modals.showAnalysesForAllele.data.analyses')
    let text = (allele.formatted.hgvsc || allele.formatted.hgvsg) + '\n'
    text += analyses.map((a) => a.name).join('\n')
    clipboard.copy(text)
}
