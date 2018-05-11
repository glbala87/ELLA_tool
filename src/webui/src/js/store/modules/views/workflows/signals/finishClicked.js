import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import saveInterpretation from '../sequences/saveInterpretation'
import finishWorkflow from '../factories/finishWorkflow'
import toastr from '../../../../common/factories/toastr'
import showModal from '../../../../common/actions/showModal'

export default [set(props`modalName`, 'finishConfirmation'), showModal]
