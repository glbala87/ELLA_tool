import { parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import toastr from '../../../../common/factories/toastr'
import getAlleleIdsByGene from '../actions/getAlleleIdsByGene'

export default [
    set(state`modals.addExcludedAlleles.show`, true),
    set(
        state`modals.addExcludedAlleles.excludedAlleleIds`,
        state`views.workflows.interpretation.selected.excluded_allele_ids`
    ),
    getAlleleIdsByGene,
    {
        success: [set(state`modals.addExcludedAlleles.data.alleleIdsByGene`, props`result`)],
        error: [toastr('error', 'Failed to load variants')]
    }
]
