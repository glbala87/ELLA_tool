import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDirty from '../../../interpretation/actions/setDirty'
import setReferenceAssessment from '../../../interpretation/actions/setReferenceAssessment'
import loadAcmg from '../../../sequences/loadAcmg'

export default [
    set(props`alleleId`, state`views.workflows.selectedAllele`),
    set(props`referenceId`, state`views.workflows.modals.evaluateReference.referenceId`),
    ({ props }) => {
        console.log('Setting with props: ')
        console.log(props)
    },
    setDirty,
    setReferenceAssessment,
    loadAcmg,
    set(state`views.workflows.modals.evaluateReference`, { show: false })
]
