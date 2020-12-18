import { set, debounce } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import loadResults from '../sequences/loadResults'

export default [
    set(module`page`, props`page`),
    debounce(500),
    {
        continue: loadResults,
        discard: []
    }
]
