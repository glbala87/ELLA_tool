import filterClassified from '../../computed/filterClassified'
import sortAlleles from '../../computed/sortAlleles'

export default function sortSections({ state, props, resolve }) {
    const orderBy = state.get('views.workflows.alleleSidebar.orderBy')
    const alleles = state.get('views.workflows.data.alleles')

    let unclassified = resolve.value(filterClassified(true, alleles))
    let classified = resolve.value(filterClassified(false, alleles))

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

    state.set('views.workflows.alleleSidebar.unclassified', unclassified.map(a => a.id))
    state.set('views.workflows.alleleSidebar.classified', classified.map(a => a.id))
}
