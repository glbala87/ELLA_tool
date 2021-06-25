import { set, debounce } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import loadAnnotationConfigs from '../sequences/loadAnnotationConfigs'

export default [
    debounce(300),
    {
        continue: [
            set(state`views.workflows.modals.addExcludedAlleles.selectedPage`, props`selectedPage`),
            loadExcludedAlleles,
            loadAnnotationConfigs
        ],
        discard: []
    }
]
