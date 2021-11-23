import filterClassified from '../../computed/filterClassified'
import sortAlleles from '../../computed/sortAlleles'
import filterTechnical from '../../computed/filterTechnical'
import filterNotRelevant from '../../computed/filterNotRelevant'

export default function sortSections({ state, resolve }) {
    const orderBy = state.get('views.workflows.alleleSidebar.orderBy')
    const caller_type_selected = state.get('views.workflows.alleleSidebar.callerTypeSelected')
    const alleles = Object.values(state.get('views.workflows.interpretation.data.alleles'))

    // Technical takes presedence over not relevant
    let technical = filterTechnical(false, alleles)
    const notTechnical = filterTechnical(true, alleles)
    let notRelevant = filterNotRelevant(false, notTechnical)
    const toClassify = filterNotRelevant(true, notTechnical)
    let unclassified = filterClassified(true, toClassify)
    let classified = filterClassified(false, toClassify)

    function genomicPosition() {
        // default sort strategy for cnv's are by chromosome and position
        if (caller_type_selected === 'cnv') {
            return 'chromosome'
        } else return null
    }

    function keyIsRelevant(key) {
        // We don't want to change the ordering when switching back to snv, if any
        // of these keys are selected in cnv mode
        if (
            caller_type_selected === 'snv' &&
            (key === 'chromosome' || key === 'sv_len' || key === 'sv_type')
        ) {
            return false
        } else return true
    }

    if (orderBy.unclassified.key && keyIsRelevant(orderBy.unclassified.key)) {
        unclassified = resolve.value(
            sortAlleles(unclassified, orderBy.unclassified.key, orderBy.unclassified.reverse)
        )
    } else {
        unclassified = resolve.value(sortAlleles(unclassified, genomicPosition(), null))
    }

    if (orderBy.classified.key && keyIsRelevant(orderBy.classified.key)) {
        classified = resolve.value(
            sortAlleles(classified, orderBy.classified.key, orderBy.classified.reverse)
        )
    } else {
        classified = resolve.value(sortAlleles(classified, 'classification', true))
    }

    if (orderBy.technical.key && keyIsRelevant(orderBy.technical.key)) {
        technical = resolve.value(
            sortAlleles(technical, orderBy.technical.key, orderBy.technical.reverse)
        )
    } else {
        technical = resolve.value(sortAlleles(technical, genomicPosition(), null))
    }

    if (orderBy.notRelevant.key && keyIsRelevant(orderBy.notRelevant.key)) {
        notRelevant = resolve.value(
            sortAlleles(notRelevant, orderBy.notRelevant.key, orderBy.notRelevant.reverse)
        )
    } else {
        notRelevant = resolve.value(sortAlleles(notRelevant, genomicPosition(), null))
    }

    state.set('views.workflows.alleleSidebar.unclassified', unclassified.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.classified', classified.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.technical', technical.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.notRelevant', notRelevant.map((a) => a.id))
}
