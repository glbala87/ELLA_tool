export default function postCustomAnnotation({ state, http, path, props }) {
    const payload = {
        allele_id: props.alleleId,
        annotations: props.customAnnotationData,
        user_id: state.get('app.user.id')
    }
    console.log(payload)

    return http
        .post(`customannotations/`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
