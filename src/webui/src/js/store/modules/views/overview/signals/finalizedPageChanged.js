import { set } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import loadFinalized from '../sequences/loadFinalized'

export default [
    set(module`section.${props`section`}.finalized.selectedPage`, props`page`),
    loadFinalized
]
