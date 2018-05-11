import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import checkAndSetValidSection from '../actions/checkAndSetValidSection'

import redirectToSection from '../actions/redirectToSection'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import loadOverviewState from '../actions/loadOverviewState'
import interval from '../../../../common/factories/interval'
import loadOverview from '../sequences/loadOverview'

const UPDATE_IMPORT_STATUS_INTERVAL = 30
const UPDATE_OVERVIEW_INTERVAL = 60

export default sequence('routed', [
    setNavbarTitle(null),
    loadOverviewState,
    checkAndSetValidSection,
    {
        valid: [
            interval(
                'start',
                'views.overview.updateImportJobCountTriggered',
                {},
                UPDATE_IMPORT_STATUS_INTERVAL * 1000,
                true
            ),
            interval(
                'start',
                'views.overview.updateOverviewTriggered',
                {},
                UPDATE_OVERVIEW_INTERVAL * 1000,
                false
            ),
            loadOverview
        ],
        invalid: [redirectToSection]
    }
])
