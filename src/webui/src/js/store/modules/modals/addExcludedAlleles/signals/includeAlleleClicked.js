import { push } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import loadIncludedAlleles from '../sequences/loadIncludedAlleles'

export default [
    push(state`modals.addExcludedAlleles.includedAlleleIds`, props`alleleId`),
    loadExcludedAlleles,
    loadIncludedAlleles
]
