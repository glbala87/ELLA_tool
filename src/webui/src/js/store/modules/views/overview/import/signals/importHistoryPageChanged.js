import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadImportHistory from '../sequences/loadImportHistory'

export default [
    set(state`views.overview.import.importHistoryPage`, props`importHistoryPage`),
    loadImportHistory
]
