import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'

export default [
    // Copy current selection from loaded data
    ({ state, props }) => {
        const { alleleId } = props
        // Filter down list to external databases for this allele's gene(s) only
        const alleleHgncIds = state
            .get(`views.workflows.interpretation.data.alleles.${alleleId}.annotation.filtered`)
            .map((x) => x.hgnc_id)

        const annotationGroups = state.get(`app.config.custom_annotation.external`).filter((x) => {
            if ('only_for_genes' in x) {
                return x.only_for_genes.some((g) => alleleHgncIds.includes(g))
            } else {
                return true
            }
        })
        state.set(`views.workflows.modals.addExternal.annotationGroups`, annotationGroups)
        state.set(`views.workflows.modals.addExternal.hgncIds`, alleleHgncIds)
        const annotation = state.get(
            `views.workflows.interpretation.data.alleles.${alleleId}.annotation`
        )
        // fetch the annotation from the state and remove keys that are not in the group
        //   to avoid POSTing non-custom annoation
        let annotationExt = annotation.hasOwnProperty('external')
            ? deepCopy(annotation.external)
            : {}
        const annotationGroupKeys = annotationGroups.map((e) => e.key)
        annotationExt = Object.entries(annotationExt)
            .filter(([k, v]) => annotationGroupKeys.includes(k))
            .reduce((obj, [k, v]) => {
                obj[k] = v
                return obj
            }, {})
        state.set(`views.workflows.modals.addExternal.selection`, annotationExt)
    },
    set(state`views.workflows.modals.addExternal.alleleId`, props`alleleId`),
    set(state`views.workflows.modals.addExternal.show`, true)
]
