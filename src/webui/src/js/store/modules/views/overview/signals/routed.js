import { sequence, parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import checkAndSetValidSection from '../actions/checkAndSetValidSection'
import changeSection from './changeSection'
import progress from '../../../../common/factories/progress'
import toastr from '../../../../common/factories/toastr'

import getOverviewAnalyses from '../actions/getOverviewAnalyses'
import getOverviewAnalysesByFindings from '../actions/getOverviewAnalysesByFindings'
import getOverviewAlleles from '../actions/getOverviewAlleles'
import loadFinalized from '../sequences/loadFinalized'
import redirectToSection from '../actions/redirectToSection'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import loadOverviewState from '../actions/loadOverviewState'

export default sequence('routed', [
    setNavbarTitle(null),
    progress('start'),
    loadOverviewState,
    checkAndSetValidSection,
    {
        valid: [
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
                    loadFinalized
                ]),
                analyses: parallel('loadOverviewAnalysis', [
                    getOverviewAnalyses,
                    {
                        success: [set(module`data.analyses`, props`result`)],
                        error: [toastr('error', 'Failed to load analyses')]
                    },
                    loadFinalized
                ]),
                'analyses-by-findings': parallel('loadOverviewAnalysisByFindings', [
                    getOverviewAnalysesByFindings,
                    {
                        success: [set(module`data.analyses`, props`result`)],
                        error: [toastr('error', 'Failed to load analyses')]
                    },
                    loadFinalized
                ]),
                otherwise: [toastr('error', 'Invalid section')]
            }
        ],
        invalid: [redirectToSection]
    },
    progress('done')
])
