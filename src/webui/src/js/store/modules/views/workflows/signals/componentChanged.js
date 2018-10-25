import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../alleleSidebar/actions/prepareSelectedAllele'
import selectedAlleleChanged from '../alleleSidebar/signals/selectedAlleleChanged'

export default [
    set(state`views.workflows.selectedComponent`, props`selectedComponent`),
    prepareSelectedAllele,
    when(state`views.workflows.selectedAllele`),
    {
        true: [selectedAlleleChanged],
        false: []
    }
]
