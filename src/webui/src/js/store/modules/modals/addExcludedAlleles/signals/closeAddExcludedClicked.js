import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import closeModal from '../../../../common/actions/closeModal'
import loadAlleles from '../../../views/workflows/sequences/loadAlleles'
import loadVisualization from '../../../views/workflows/visualization/sequences/loadVisualization'

export default [
    set(state`views.workflows.interpretation.state.manuallyAddedAlleles`, props`includedAlleleIds`),
    set(props`modalName`, 'addExcludedAlleles'),
    closeModal,
    loadAlleles, // Reload workflows alleles
    loadVisualization
]
