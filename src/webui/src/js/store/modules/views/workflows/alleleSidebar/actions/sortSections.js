import filterClassified from '../../computed/filterClassified'
import sortAlleles from '../../computed/sortAlleles'
import filterTechnical from '../../computed/filterTechnical'

export default function sortSections({ state, props, resolve }) {
    const orderBy = state.get('views.workflows.alleleSidebar.orderBy')
    let alleles = Object.values(state.get('views.workflows.data.alleles'))

    const notTechnical = filterTechnical(true, alleles)
    let technical = filterTechnical(false, alleles)
    let unclassified = resolve.value(filterClassified(true, notTechnical))
    let classified = resolve.value(filterClassified(false, notTechnical))

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

    state.set('views.workflows.alleleSidebar.unclassified', unclassified.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.classified', classified.map((a) => a.id))
    state.set('views.workflows.alleleSidebar.technical', technical.map((a) => a.id))
}
