import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(state`views.overview.import.jobData`, props`jobData`),
    () => {
        console.log('jobData updated')
    }
]
