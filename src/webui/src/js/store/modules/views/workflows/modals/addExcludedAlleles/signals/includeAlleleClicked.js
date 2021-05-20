import { push } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'

export default [
    push(state`views.workflows.modals.addExcludedAlleles.includedAlleleIds`, props`alleleId`),
    loadExcludedAlleles
]
