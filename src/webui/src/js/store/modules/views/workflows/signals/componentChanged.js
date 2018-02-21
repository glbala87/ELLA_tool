import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../alleleSidebar/actions/prepareSelectedAllele'

export default [
    set(state`views.workflows.selectedComponent`, props`selectedComponent`),
    prepareSelectedAllele
]
