import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadSelectedGenepanel from '../sequences/loadSelectedGenepanel'

export default [
    set(state`views.overview.import.selectedGenepanel`, props`genepanel`),
    loadSelectedGenepanel
]
