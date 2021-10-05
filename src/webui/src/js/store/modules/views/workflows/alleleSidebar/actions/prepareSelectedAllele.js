export default function prepareSelectedAllele({ state }) {
    const selectedComponent = state.get('views.workflows.selectedComponent')
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const unclassified = state.get('views.workflows.alleleSidebar.unclassified')
    const classified = state.get('views.workflows.alleleSidebar.classified')
    const technical = state.get('views.workflows.alleleSidebar.technical')
    const notRelevant = state.get('views.workflows.alleleSidebar.notRelevant')
    const caller_type_selected = state
        .get('views.workflows.alleleSidebar.callerTypeSelected')
        .toUpperCase()
    let selectedAllele = state.get('views.workflows.selectedAllele')
    if (selectedComponent !== 'Classification') {
        state.set('views.workflows.selectedAllele', null)
        return
    }

    // If already selected and it's still valid selection, do nothing
    if (selectedAllele && selectedAllele in alleles) {
        return
    }

    if (unclassified.length) {
        const snv_unclassified = unclassified.filter(
            (id) => alleles[id].caller_type == caller_type_selected
        )
        state.set('views.workflows.selectedAllele', snv_unclassified[0])
    } else if (classified.length) {
        const snv_classified = classified.filter(
            (id) => alleles[id].caller_type == caller_type_selected
        )
        state.set('views.workflows.selectedAllele', snv_classified[0])
    } else if (technical.length) {
        const snv_technical = technical.filter(
            (id) => alleles[id].caller_type == caller_type_selected
        )
        state.set('views.workflows.selectedAllele', snv_technical[0])
    } else if (notRelevant.length) {
        const snv_notRelevant = notRelevant.filter(
            (id) => alleles[id].caller_type == caller_type_selected
        )
        state.set('views.workflows.selectedAllele', snv_notRelevant[0])
    } else {
        state.set('views.workflows.selectedAllele', null)
    }
}
