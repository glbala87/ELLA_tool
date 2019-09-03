import { sequence } from 'cerebral'

import redirectToSection from '../actions/redirectToSection'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import loadOverviewState from '../actions/loadOverviewState'
import interval from '../../../../common/factories/interval'
import loadOverview from '../sequences/loadOverview'
import setSections from '../actions/setSections'
import checkAndSelectValidSection from '../actions/checkAndSelectValidSection'

const UPDATE_OVERVIEW_INTERVAL = 180

export default sequence('routed', [
    setNavbarTitle(null),
    loadOverviewState,
    setSections,
    checkAndSelectValidSection,
    {
        valid: [
            // Unset by changeView
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
