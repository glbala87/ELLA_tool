import { parallel } from 'cerebral'
import { push, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadAlleles from '../sequences/loadAlleles'
import loadIncludedAlleles from '../sequences/loadIncludedAlleles'

export default [
    push(state`modals.addExcludedAlleles.includedAlleleIds`, props`alleleId`),
    loadAlleles,
    loadIncludedAlleles
]
