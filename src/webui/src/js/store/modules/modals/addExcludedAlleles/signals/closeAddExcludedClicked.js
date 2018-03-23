import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import closeModal from '../../../../common/actions/closeModal'
import loadAlleles from '../../../views/workflows/sequences/loadAlleles'

export default [
    set(
        state`views.workflows.interpretation.selected.state.manuallyAddedAlleles`,
        props`includedAlleleIds`
    ),
    set(props`modalName`, 'addExcludedAlleles'),
    closeModal,
    loadAlleles // Reload workflows alleles
]
