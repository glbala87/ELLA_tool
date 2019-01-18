export default function copySelectedAlamut({ state, clipboard }) {
    const selectedAllele = state.get('views.workflows.selectedAllele')
    const allele = state.get(`views.workflows.interpretation.data.alleles.${selectedAllele}`)
    clipboard.copy(allele.formatted.alamut)
}
