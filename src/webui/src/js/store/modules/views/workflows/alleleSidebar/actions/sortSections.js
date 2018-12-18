import filterClassified from '../../computed/filterClassified'
import sortAlleles from '../../computed/sortAlleles'
import filterTechnical from '../../computed/filterTechnical'
import filterNotRelevant from '../../computed/filterNotRelevant'

export default function sortSections({ state, resolve }) {
    const orderBy = state.get('views.workflows.alleleSidebar.orderBy')
    const alleles = Object.values(state.get('views.workflows.data.alleles'))

    // Technical takes presedence over not relevant
    let technical = filterTechnical(false, alleles)
    const notTechnical = filterTechnical(true, alleles)
    let notRelevant = filterNotRelevant(false, notTechnical)
    const toClassify = filterNotRelevant(true, notTechnical)
    let unclassified = filterClassified(true, toClassify)
    let classified = filterClassified(false, toClassify)

    if (orderBy.unclassified.key) {
        unclassified = resolve.value(
            sortAlleles(unclassified, orderBy.unclassified.key, orderBy.unclassified.reverse)
        )
    } else {
        unclassified = resolve.value(sortAlleles(unclassified, null, null))
    }

    if (orderBy.classified.key) {
        classified = resolve.value(
            sortAlleles(classified, orderBy.classified.key, orderBy.classified.reverse)
        )
    } else {
        classified = resolve.value(sortAlleles(classified, 'classification', true))
    }

    if (orderBy.technical.key) {
        technical = resolve.value(
            sortAlleles(technical, orderBy.technical.key, orderBy.technical.reverse)
        )
    } else {
        technical = resolve.value(sortAlleles(technical, null, null))
    }

    if (orderBy.notRelevant.key) {
        notRelevant = resolve.value(
            sortAlleles(notRelevant, orderBy.notRelevant.key, orderBy.notRelevant.reverse)
        )
    } else {
        notRelevant = resolve.value(sortAlleles(notRelevant, null, null))
    }

    state.set('views.workflows.alleleSidebar.unclassified', unclassified.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.classified', classified.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.technical', technical.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.notRelevant', notRelevant.map((a) => a.id))
}
