import { set, equals } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import getOverviewAllelesFinalized from '../actions/getOverviewAllelesFinalized'
import getOverviewAnalysesFinalized from '../actions/getOverviewAnalysesFinalized'
import toast from '../../../../common/factories/toast'

const analysesFinalized = [
    getOverviewAnalysesFinalized,
    {
        success: [set(module`data.analysesFinalized`, props`result`)],
        error: [toast('error', 'Failed to load finished analyses')]
    }
]

export default [
    equals(props`section`),
    {
        variants: [
            getOverviewAllelesFinalized,
            {
                success: [set(module`data.allelesFinalized`, props`result`)],
                error: [toast('error', 'Failed to load finished variants')]
            }
        ],
        analyses: analysesFinalized,
        'analyses-by-classified': analysesFinalized,
        otherwise: [toast('error', 'Unknown section')]
    }
]
