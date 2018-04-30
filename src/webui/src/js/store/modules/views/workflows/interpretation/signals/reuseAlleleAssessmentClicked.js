import { when, set, toggle } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import isAlleleAssessmentOutdated from '../operators/isAlleleAssessmentOutdated'
import toggleReuseReferenceAssessments from '../actions/toggleReuseReferenceAssessments'
import toastr from '../../../../../common/factories/toastr'
import setDirty from '../actions/setDirty'

export default [
    isAlleleAssessmentOutdated,
    {
        true: [
            toastr('error', 'Cannot toggle reuse of outdated classification')
        ],
        false: [
            toggle(module`selected.state.allele.${props`alleleId`}.alleleassessment.reuse`),
            toggleReuseReferenceAssessments // Reuse of referenceassessments are tied to alleleassessment
        ]
    }
]
