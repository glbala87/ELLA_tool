import { props, state } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'

export default [
    ({ props, state }) => {
        let { index, key, value } = props
        if (value === undefined) {
            value = null
        }
        if (typeof value === 'object') {
            value = deepCopy(value)
        }
        console.log(index, key, value)
        state.set(`views.overview.import.user.jobData.${index}.selection.${key}`, value)
    }
]
