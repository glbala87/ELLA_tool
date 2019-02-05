import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setManuallyAddedAlleleIds from '../actions/setManuallyAddedAlleleIds'
import loadAlleles from '../../../sequences/loadAlleles'
import loadVisualization from '../../../visualization/sequences/loadVisualization'

export default [
    setManuallyAddedAlleleIds,
    set(state`views.workflows.modals.addExcludedAlleles.show`, false),
    loadAlleles,
    loadVisualization
]
