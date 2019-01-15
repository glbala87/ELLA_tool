import { sequence } from 'cerebral'
import toast from '../../../../common/factories/toast'
import getAcmgCodes from '../actions/getAcmgCodes'
import prepareSuggestedAcmg from '../actions/prepareSuggestedAcmg'

export default sequence('loadAcmg', [
    getAcmgCodes,
    {
        success: [
            ({ props, state }) => {
                const alleles = state.get('views.workflows.interpretation.data.alleles')
                const acmgResult = props.result
                for (let [aId, aAcmg] of Object.entries(acmgResult)) {
                    state.set(`views.workflows.interpretation.data.alleles.${aId}.acmg`, aAcmg)
                }
            },
            prepareSuggestedAcmg
        ],
        error: [toast('error', 'Failed to load ACMG codes', 30000)]
    }
])
