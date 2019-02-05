export default function copyAnalysesForAlleleClipboard({ state, clipboard }) {
    const allele = state.get('search.modals.showAnalysesForAllele.allele')
    const analyses = state.get('search.modals.showAnalysesForAllele.data.analyses')
    let text = allele.formatted.display + '\n'
    text += analyses.map((a) => a.name).join('\n')
    clipboard.copy(text)
}
