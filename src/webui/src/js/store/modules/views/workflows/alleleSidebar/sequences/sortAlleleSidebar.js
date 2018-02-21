import { Compute, sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterClassified from '../../computed/filterClassified'
import sortAlleleSidebar from '../computed/sortAlleleSidebar'

export default sequence('sortAlleleSidebar', [
    set(
        state`views.workflows.alleleSidebar.unclassified`,
        Compute(
            sortAlleleSidebar(filterClassified(true, state`views.workflows.data.alleles`)),
            alleles => alleles.map(a => a.id)
        )
    ),
    set(
        state`views.workflows.alleleSidebar.classified`,
        Compute(
            sortAlleleSidebar(filterClassified(false, state`views.workflows.data.alleles`)),
            alleles => alleles.map(a => a.id)
        )
    )
])
