import { merge } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAnalyses from '../actions/filterAnalyses'

export default [merge(state`views.overview.filter`, props`filter`), filterAnalyses]
