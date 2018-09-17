import { set, when, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../alleleSidebar/actions/prepareSelectedAllele'
import updateSuggestedClassification from '../interpretation/sequences/updateSuggestedClassification'
import updateIgvLocus from '../visualization/actions/updateIgvLocus'
import loadVisualization from '../visualization/sequences/loadVisualization'

export default [
    set(state`views.workflows.selectedComponent`, props`selectedComponent`),
    prepareSelectedAllele,
    equals(props`selectedComponent`),
    {
        Visualization: [loadVisualization],
        otherwise: []
    },
    when(state`views.workflows.selectedAllele`),
    {
        true: [
            set(props`alleleId`, state`views.workflows.selectedAllele`),
            updateSuggestedClassification,
            updateIgvLocus
        ],
        false: []
    }
]
