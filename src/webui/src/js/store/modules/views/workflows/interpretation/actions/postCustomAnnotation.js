import { deepCopy } from '../../../../../../util'

export default function postCustomAnnotation({ state, http, path, props }) {
    const customAnnotationDataPruned = deepCopy(props.customAnnotationData)
    // filter - use only entries that have non-null sub-properties
    //   example: `{prediction: {ortholog_conservation: null, dna_conservation: null}}`
    //        =>  `{prediction: {}}`
    Object.keys(customAnnotationDataPruned).forEach((grpk) => {
        customAnnotationDataPruned[grpk] = Object.entries(customAnnotationDataPruned[grpk])
            .filter(([k, v]) => v !== null)
            .reduce((obj, [k, v]) => {
                obj[k] = v
                return obj
            }, {})
    })

    const payload = {
        allele_id: props.alleleId,
        annotations: customAnnotationDataPruned,
        user_id: state.get('app.user.id')
    }

    return http
        .post(`customannotations/`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
