import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import closeModal from '../../../../common/actions/closeModal'
import loadAlleles from '../../../views/workflows/sequences/loadAlleles'
import loadVisualization from '../../../views/workflows/visualization/sequences/loadVisualization'
import setManuallyAddedAlleleIds from '../actions/setManuallyAddedAlleleIds'

export default [
    setManuallyAddedAlleleIds,
    set(props`modalName`, 'addExcludedAlleles'),
    closeModal,
    loadAlleles, // Reload workflows alleles
    loadVisualization
]
