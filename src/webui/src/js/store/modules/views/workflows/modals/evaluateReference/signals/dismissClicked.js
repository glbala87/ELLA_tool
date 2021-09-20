import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDirty from '../../../interpretation/actions/setDirty'
import setReferenceAssessment from '../../../interpretation/actions/setReferenceAssessment'
import canUpdateReferenceAssessment from '../../../interpretation/operators/canUpdateReferenceAssessment'
import loadAcmg from '../../../sequences/loadAcmg'

export default [
    set(props`alleleId`, state`views.workflows.selectedAllele`),
    set(props`referenceId`, state`views.workflows.modals.evaluateReference.referenceId`),
    canUpdateReferenceAssessment,
    {
        true: [setDirty, setReferenceAssessment, loadAcmg],
        false: []
    },
    set(state`views.workflows.modals.evaluateReference`, { show: false })
]
