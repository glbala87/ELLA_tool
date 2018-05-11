import { sequence, parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import getOverviewAnalyses from '../actions/getOverviewAnalyses'
import getOverviewAnalysesByFindings from '../actions/getOverviewAnalysesByFindings'
import getOverviewAlleles from '../actions/getOverviewAlleles'
import loadFinalized from '../sequences/loadFinalized'
import progress from '../../../../common/factories/progress'
import toastr from '../../../../common/factories/toastr'

export default sequence('loadOverview', [
    progress('start'),

    equals(props`section`),
    {
        // section comes from url
        variants: parallel('loadOverviewAlleles', [
            getOverviewAlleles,
            {
                success: [set(module`data.alleles`, props`result`)],
                error: [toastr('error', 'Failed to load variants')]
            },
            [set(props`page`, 1), loadFinalized]
        ]),
        analyses: parallel('loadOverviewAnalysis', [
            getOverviewAnalyses,
            {
                success: [set(module`data.analyses`, props`result`)],
                error: [toastr('error', 'Failed to load analyses')]
            },
            [set(props`page`, 1), loadFinalized]
        ]),
        'analyses-by-findings': parallel('loadOverviewAnalysisByFindings', [
            getOverviewAnalysesByFindings,
            {
                success: [set(module`data.analyses`, props`result`)],
                error: [toastr('error', 'Failed to load analyses')]
            },
            [set(props`page`, 1), loadFinalized]
        ]),
        otherwise: [toastr('error', 'Invalid section')]
    },
    progress('done')
])
