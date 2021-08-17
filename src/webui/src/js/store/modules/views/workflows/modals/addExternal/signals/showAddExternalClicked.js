import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'

export default [
    // Copy current selection from loaded data
    ({ state, props }) => {
        const { alleleId } = props
        const annotation = state.get(
            `views.workflows.interpretation.data.alleles.${alleleId}.annotation`
        )
        const annotationExt = annotation.hasOwnProperty('external')
            ? deepCopy(annotation.external)
            : {}
        state.set(`views.workflows.modals.addExternal.selection`, annotationExt)
    },
    // Filter down list to external databases for this allele's gene(s) only
    ({ state, props }) => {
        const { alleleId } = props
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
    },
    set(state`views.workflows.modals.addExternal.alleleId`, props`alleleId`),
    set(state`views.workflows.modals.addExternal.show`, true)
]
