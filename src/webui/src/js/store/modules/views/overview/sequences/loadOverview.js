import { sequence, parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import getOverviewAnalyses from '../actions/getOverviewAnalyses'
import getOverviewAnalysesByFindings from '../actions/getOverviewAnalysesByFindings'
import getOverviewAlleles from '../actions/getOverviewAlleles'
import loadFinalized from '../sequences/loadFinalized'
import progress from '../../../../common/factories/progress'
import toast from '../../../../common/factories/toast'
import loadImport from '../import/sequences/loadImport'
import interval from '../../../../common/factories/interval'

const UPDATE_IMPORT_STATUS_INTERVAL = 30

export default sequence('loadOverview', [
    progress('start'),
    interval('stop', 'views.overview.import.updateImportJobsTriggered'),
    equals(props`section`),
    {
        // section comes from url
        variants: parallel('loadOverviewAlleles', [
            getOverviewAlleles,
            {
                success: [set(module`data.alleles`, props`result`)],
                error: [toast('error', 'Failed to load variants')]
            },
            [set(props`page`, 1), loadFinalized]
        ]),
        analyses: parallel('loadOverviewAnalysis', [
            getOverviewAnalyses,
            {
                success: [set(module`data.analyses`, props`result`)],
                error: [toast('error', 'Failed to load analyses')]
            },
            [set(props`page`, 1), loadFinalized]
        ]),
        import: [
            // Also unset in changeView (plus above)
            interval(
                'start',
                'views.overview.import.updateImportJobsTriggered',
                {},
                UPDATE_IMPORT_STATUS_INTERVAL * 1000,
                false
            ),
            loadImport
        ],
        'analyses-by-findings': parallel('loadOverviewAnalysisByFindings', [
            getOverviewAnalysesByFindings,
            {
                success: [set(module`data.analyses`, props`result`)],
                error: [toast('error', 'Failed to load analyses')]
            },
            [set(props`page`, 1), loadFinalized]
        ]),
        otherwise: [toast('error', 'Invalid section')]
    },
    progress('done')
])
