import { default as commonIsAlleleAssessmentOutdated } from '../../../../../common/computes/isAlleleAssessmentOutdated'

export default function isAlleleAssessmentOutdated({ state, path, props, resolve }) {
    if (!props.alleleId) {
        throw Error('Missing required props alleleId')
    }
    const allele = state.get(`views.workflows.interpretation.data.alleles.${props.alleleId}`)
    if (resolve.value(commonIsAlleleAssessmentOutdated(allele))) {
        return path.true()
    }
    return path.false()
}
