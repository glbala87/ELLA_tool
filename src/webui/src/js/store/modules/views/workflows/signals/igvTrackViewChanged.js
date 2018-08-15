import { set, when, toggle } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    toggle(state`views.workflows.igv.tracks.${props`index`}.show`),
]
