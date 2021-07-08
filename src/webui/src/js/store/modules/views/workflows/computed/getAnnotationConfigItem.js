import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'

export default Compute(
    state`views.workflows.data.annotationConfigs`,
    state`views.workflows.modals.addExcludedAlleles.data.annotationConfigs`,
    props`annotationConfigId`,
    props`annotationConfigItemIdx`,
    (
        annotationConfigs,
        excludedModalAnnotationConfigs,
        annotationConfigId,
        annotationConfigItemIdx
    ) => {
        if (annotationConfigs === undefined) {
            return null
        }

        // If annotationConfig is not in the annotationConfigs array, this must mean that we are
        // looking at popups in the addExcludedModal (which might have a different set of annotation configs
        // loaded). It is irrelevant which state source is used to find the config.
        let annotationConfig = annotationConfigs.find((x) => x.id === annotationConfigId)

        if (!annotationConfig) {
            annotationConfig = excludedModalAnnotationConfigs.find(
                (x) => x.id === annotationConfigId
            )
        }
        return annotationConfig.view[annotationConfigItemIdx].config
    }
)
