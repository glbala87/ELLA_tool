import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toastr from '../../../../common/factories/toastr'
import showAddExcludedModal from '../actions/showAddExcludedModal'
import loadInterpretationData from '../signals/loadInterpretationData'

export default [
    showAddExcludedModal,
    set(
        state`views.workflows.interpretation.selected.state.manuallyAddedAlleles`,
        props`manuallyAddedAlleles`
    ),
    loadInterpretationData
]
