import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getConfig from '../actions/getConfig'

export default [
    getConfig,
    {
        success: [set(state`app.config`, props`result`)],
        error: [set(state`app.config`, null)]
    }
]
