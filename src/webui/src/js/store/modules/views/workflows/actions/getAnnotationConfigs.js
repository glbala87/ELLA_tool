const getAnnotationConfigs = (allelePath) => {
    return ({ http, path, state }) => {
        const alleles = state.get(allelePath)
        if (!alleles || !Object.keys(alleles).length) {
            return path.success({ result: [] })
        }

        const annotationConfigIds = new Set(
            Object.values(alleles).map((x) => x.annotation.annotation_config_id)
        )

        return http
            .get(
                `annotationconfigs/?annotation_config_ids=${Array.from(annotationConfigIds).join(
                    ','
                )}`
            )
            .then((response) => {
                return path.success({ result: response.result })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    }
}

export default getAnnotationConfigs
