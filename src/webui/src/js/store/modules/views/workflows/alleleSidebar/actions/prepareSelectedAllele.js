export default function prepareSelectedAllele({ state }) {
    const selectedComponent = state.get('views.workflows.selectedComponent')
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const caller_type_selected = state.get('views.workflows.alleleSidebar.callerTypeSelected')
    let selectedAllele = state.get('views.workflows.selectedAllele')

    const unclassified = state
        .get('views.workflows.alleleSidebar.unclassified')
        .filter((id) => alleles[id].caller_type == caller_type_selected)
    const classified = state
        .get('views.workflows.alleleSidebar.classified')
        .filter((id) => alleles[id].caller_type == caller_type_selected)
    const technical = state
        .get('views.workflows.alleleSidebar.technical')
        .filter((id) => alleles[id].caller_type == caller_type_selected)
    const notRelevant = state
        .get('views.workflows.alleleSidebar.notRelevant')
        .filter((id) => alleles[id].caller_type == caller_type_selected)

    if (selectedComponent !== 'Classification') {
        state.set('views.workflows.selectedAllele', null)
        return
    }

    // If already selected and it's still valid selection, do nothing
    if (
        selectedAllele &&
        selectedAllele in alleles &&
        alleles[selectedAllele].caller_type === caller_type_selected
    ) {
        return
    }

    if (unclassified.length) {
        state.set('views.workflows.selectedAllele', unclassified[0])
    } else if (classified.length) {
        state.set('views.workflows.selectedAllele', classified[0])
    } else if (technical.length) {
        state.set('views.workflows.selectedAllele', technical[0])
    } else if (notRelevant.length) {
        state.set('views.workflows.selectedAllele', notRelevant[0])
    } else {
        state.set('views.workflows.selectedAllele', null)
    }
}
