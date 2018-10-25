import { parallel } from 'cerebral'
import { push, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import loadIncludedAlleles from '../sequences/loadIncludedAlleles'

export default [
    push(state`modals.addExcludedAlleles.includedAlleleIds`, props`alleleId`),
    loadExcludedAlleles,
    loadIncludedAlleles
]
