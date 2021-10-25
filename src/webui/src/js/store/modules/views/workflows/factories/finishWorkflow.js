import { prepareInterpretationPayload } from '../../../../common/helpers/workflow'
import getAlleleIdsFromInterpretation from '../computed/getAlleleIdsFromInterpretation'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

const ACTIONS = {
    'Not ready': 'marknotready',
    Interpretation: 'markinterpretation',
    Review: 'markreview',
    'Medical review': 'markmedicalreview',
    Finalized: 'finalize'
}

export default function(finishType) {
    return function finishWorkflow({ state, http, path, resolve }) {
        const type = state.get('views.workflows.type')
        const postType = TYPES[type]
        const id = state.get('views.workflows.id')
        const alleles = state.get('views.workflows.interpretation.data.alleles')
        const currentState = state.get('views.workflows.interpretation.state')
        const alleleIds = resolve.value(getAlleleIdsFromInterpretation)

        const excludedAlleleIdsByCallerType = state.get(
            'views.workflows.interpretation.data.filteredAlleleIds.excluded_alleles_by_caller_type'
        )

        /**
         * In the front end, we have two interpretation modes: cnv and snv, and the
         * excluded alleles are operated on separately for each mode, input for
         * this loop is:
         * {
         *   excluded_alleles_by_caller_type:
         *   {
         *       snv: {
         *          region_filter: [1,2,3]
         *          // other filters
         *       },
         *       cnv: {
         *          region_filter: [23,34],
         *          // other filters
         *       }
         *
         *   }
         * }
         *
         * In the backend, there are no modes, thus we need to merge common filters of the excluded
         * alleles from the snv mode and cnv mode. Output from this loop is:
         * {
         *      excluded_alleles: {
         *          region_filter: [1,2,3,23,34]
         *      }
         * }
         */
        const excludedAlleleIds = {}
        if (excludedAlleleIdsByCallerType != null) {
            for (const excluded of Object.values(excludedAlleleIdsByCallerType)) {
                for (const [category, allele_ids] of Object.entries(excluded)) {
                    if (!(category in excludedAlleleIds)) {
                        excludedAlleleIds[category] = []
                    }
                    excludedAlleleIds[category] = excludedAlleleIds[category].concat(allele_ids)
                }
            }
        }

        try {
            const payload = prepareInterpretationPayload(
                type,
                currentState,
                alleles,
                alleleIds,
                excludedAlleleIds
            )
            return http
                .post(`workflows/${postType}/${id}/actions/${ACTIONS[finishType]}/`, payload)
                .then((response) => {
                    return path.success(response)
                })
                .catch((response) => {
                    return path.error(response)
                })
        } catch (error) {
            console.error(error)
            return path.error({ error })
        }
    }
}
