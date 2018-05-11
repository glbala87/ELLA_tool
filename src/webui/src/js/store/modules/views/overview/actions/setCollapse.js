import { deepCopy } from '../../../../../util'
import { AVAILABLE_SECTIONS } from '../getOverviewState'

export default function setCollapse({ props, state }) {
    for (let name of ['section', 'name', 'collapsed']) {
        if (!(name in props)) {
            throw Error(`Missing required prop ${name}`)
        }
    }

    state.set(`views.overview.state.${props.section}.${props.name}.collapsed`, props.collapsed)
}
