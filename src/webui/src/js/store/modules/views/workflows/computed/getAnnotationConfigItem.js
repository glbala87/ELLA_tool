import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'

export default Compute(
    state`views.workflows.data.annotationConfigs`,
    props`annotationConfigId`,
    props`annotationConfigItemIdx`,
    (annotationConfigs, annotationConfigId, annotationConfigItemIdx) => {
        return annotationConfigs.find((x) => x.id === annotationConfigId).view[
            annotationConfigItemIdx
        ].config
    }
)
