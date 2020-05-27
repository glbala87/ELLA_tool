import { set } from 'cerebral/operators'
import { state } from 'cerebral/tags'
import { DEFAULT_FILTER } from '../getOverviewState'
import filterAnalyses from '../actions/filterAnalyses'

export default [
    set(state`views.overview.filter`, Object.assign({}, DEFAULT_FILTER)),
    filterAnalyses
]
