import { set, equals } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import getOverviewAllelesFinalized from '../actions/getOverviewAllelesFinalized'
import getOverviewAnalysesFinalized from '../actions/getOverviewAnalysesFinalized'
import toastr from '../../../../common/factories/toastr'

const analysesFinalized = [
    getOverviewAnalysesFinalized,
    {
        success: [set(module`data.analysesFinalized`, props`result`)],
        error: [toastr('error', 'Failed to load finished analyses')]
    }
]

export default [
    equals(props`section`),
    {
        variants: [
            getOverviewAllelesFinalized,
            {
                success: [set(module`data.allelesFinalized`, props`result`)],
                error: [toastr('error', 'Failed to load finished variants')]
            }
        ],
        analyses: analysesFinalized,
        'analyses-by-findings': analysesFinalized
    }
]
