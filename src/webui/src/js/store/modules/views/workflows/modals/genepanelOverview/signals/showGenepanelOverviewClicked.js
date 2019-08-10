import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'
import getGenepanelStats from '../actions/getGenepanelStats'
import toast from '../../../../../../common/factories/toast'

export default [
    set(state`views.workflows.modals.genepanelOverview.show`, true),
    set(state`views.workflows.modals.genepanelOverview.name`, props`name`),
    set(state`views.workflows.modals.genepanelOverview.version`, props`version`),
    set(state`views.workflows.modals.genepanelOverview.filteredGenesPerPage`, 100),
    set(state`views.workflows.modals.genepanelOverview.filteredGenesPage`, 1),
    getGenepanel,
    {
        success: [
            set(state`views.workflows.modals.genepanelOverview.data.genepanel`, props`result`)
        ],
        error: [toast('error', 'Failed to fetch gene panel')]
    },
    getGenepanelStats,
    {
        success: [set(state`views.workflows.modals.genepanelOverview.data.stats`, props`result`)],
        error: [toast('error', 'Failed to fetch gene panel stats')]
    }
]
