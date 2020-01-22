import { prepareAlleleFinalizePayload } from '../../../../../common/helpers/workflow'
import getAlleleState from '../computed/getAlleleState'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

export default function postFinalizeAllele({ state, props, http, path, resolve }) {
    const { alleleId } = props
    const type = state.get('views.workflows.type')
    const id = state.get('views.workflows.id')
    const references = state.get('views.workflows.interpretation.data.references')
    const allele = state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
    const alleleState = resolve.value(getAlleleState(alleleId))

    try {
        const payload = prepareAlleleFinalizePayload(allele, alleleState, Object.values(references))

        return http
            .post(`workflows/${TYPES[type]}/${id}/actions/finalizeallele/`, payload)
            .then((response) => {
                return path.success(response)
            })
            .catch((response) => {
                console.error(response)
                return path.error(response)
            })
    } catch (error) {
        console.error(error)
        return path.error({ error })
    }
}
