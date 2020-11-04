import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postCustomAnnotation from '../../../../workflows/interpretation/sequences/postCustomAnnotation'

const extractPayload = ({ props }) => {
    const { customAnnotationData } = props
    console.log(customAnnotationData)
    customAnnotationData.references = Object.values(customAnnotationData.references).map((x) => {
        return { sources: ['User'], id: x.id, pubmed_id: x.pubmed_id }
    })
    console.log(customAnnotationData)
    return { customAnnotationData }
}

export default [
    extractPayload,
    postCustomAnnotation,
    set(state`views.workflows.modals.addReferences`, { show: false })
]
