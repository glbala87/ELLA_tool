import { deepCopy } from '../../../../../../util'

export default function postCustomAnnotation({ state, http, path, props }) {
    // filter - use only enrties that have non-null sub-properties
    //   example: `{prediction: {ortholog_conservation: null, dna_conservation: null}}`
    //        =>  `{}`
    const customAnnotationData = Object.entries(deepCopy(props.customAnnotationData))
        .filter((kgrp, vgrp) => {
            return Object.values(vgrp).some((e) => e !== null)
        })
        .reduce((obj, key) => {
            return {
                ...obj,
                [key]: raw[key]
            }
        }, {})

    const payload = {
        allele_id: props.alleleId,
        annotations: customAnnotationData,
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
