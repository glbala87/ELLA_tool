function getAnnotationConfigs({ http, path, state }) {
    const alleles = state.get(`views.workflows.interpretation.data.alleles`)
    if (!alleles) {
        return path.success({})
    }

    const annotationConfigIds = Object.values(alleles).map((x) => x.annotation.annotation_config_id)

    return http
        .get(
            `annotationconfigs/?annotation_config_ids=${Array.from(annotationConfigIds).join(',')}`
        )
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getAnnotationConfigs
