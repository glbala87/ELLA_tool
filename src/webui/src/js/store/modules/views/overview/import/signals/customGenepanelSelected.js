import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadCustomGenepanelData from '../sequences/loadCustomGenepanelData'
import resetImport from '../sequences/resetImport'

export default [
    set(state`views.overview.import.customGenepanel`, props`option`),
    when(state`views.overview.import.customGenepanel`),
    {
        true: [loadCustomGenepanelData, resetImport],
        false: []
    }
]
