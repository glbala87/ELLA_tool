import { deepCopy } from '../../../../../util'
import { parallel, sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAcmgCodes from '../actions/getAcmgCodes'
import prepareSuggestedAcmg from '../actions/prepareSuggestedAcmg'
import toastr from '../../../../common/factories/toastr'

export default sequence('loadAcmg', [
    getAcmgCodes,
    {
        success: [
            ({ props, state }) => {
                const alleles = state.get('views.workflows.data.alleles')
                const acmgResult = props.result
                for (let [aId, aAcmg] of Object.entries(acmgResult)) {
                    state.set(`views.workflows.data.alleles.${aId}.acmg`, aAcmg)
                }
            },
            prepareSuggestedAcmg
        ],
        error: [toastr('error', 'Failed to load ACMG codes', 30000)]
    }
])