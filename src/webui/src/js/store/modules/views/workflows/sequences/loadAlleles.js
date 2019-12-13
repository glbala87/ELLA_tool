import { sequence } from 'cerebral'
import { set, when, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAlleles from '../actions/getAlleles'
import toast from '../../../../common/factories/toast'
import prepareInterpretationState from './prepareInterpretationState'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'
import loadCollisions from './loadCollisions'
import selectedAlleleChanged from './selectedAlleleChanged'

export default sequence('loadAlleles', [
    getAlleles,
    {
        success: [
            set(state`views.workflows.interpretation.data.alleles`, props`result`),
            prepareInterpretationState,
            equals(state`views.workflows.type`),
            {
                analysis: [allelesChanged], // Analysis workflow. Update alleleSidebar
                allele: [set(state`views.workflows.selectedAllele`, state`views.workflows.id`)] // Variant workflow
            },
            loadCollisions,
            when(state`views.workflows.selectedAllele`),
            {
                true: [
                    set(props`alleleId`, state`views.workflows.selectedAllele`),
                    selectedAlleleChanged
                ],
                false: []
            }
        ],
        error: [toast('error', 'Failed to load variant(s)', 30000)]
    }
])
