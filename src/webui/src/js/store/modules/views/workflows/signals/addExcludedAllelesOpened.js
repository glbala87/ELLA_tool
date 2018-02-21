import { parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, module, props, string } from 'cerebral/tags'
import toastr from '../../../../common/factories/toastr'
import getExcludedAlleles from '../actions/getExcludedAlleles'

export default [
    set(module`modals.addExcludedAlleles.show`, true),
    set(
        module`modals.addExcludedAlleles.excludedAlleleIds`,
        module`interpretation.selected.excluded_allele_ids`
    ),
    getExcludedAlleles,
    {
        success: [
            set(module`modals.addExcludedAlleles.data.alleles`, props`result`),
            // TODO: Structure this better when we rework the slicing/fetching
            ({ module }) => {}
        ],
        error: [toastr('error', 'Failed to load variants', 10000)]
    }
]
