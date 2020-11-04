import { set, push, equals, debounce, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../../common/factories/toast'

export default [
    ({ state, props }) => {
        const { refId } = props

        var userReferenceIds = state.get(`views.workflows.modals.addReferences.userReferenceIds`)
        console.log(userReferenceIds)
        userReferenceIds = userReferenceIds.filter((x) => x !== refId)
        console.log(refId)
        console.log(userReferenceIds)
        state.set(`views.workflows.modals.addReferences.userReferenceIds`, userReferenceIds)
    }
]
