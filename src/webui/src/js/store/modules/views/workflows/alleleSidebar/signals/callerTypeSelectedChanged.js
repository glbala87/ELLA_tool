import { state, props } from 'cerebral/tags'
import { set } from 'cerebral/operators'
import prepareSelectedAllele from '../actions/prepareSelectedAllele'

export default [
    set(state`views.workflows.alleleSidebar.callerTypeSelected`, props`callerTypeSelected`),
    prepareSelectedAllele
]
