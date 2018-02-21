import { Module } from 'cerebral'

import { redirect } from '@cerebral/router/operators'
import LoginModule from './login'
import OverviewModule from './overview'
import WorkflowsModule from './workflows'
import DashboardModule from './dashboard'

export default Module({
    modules: {
        overview: OverviewModule,
        workflows: WorkflowsModule,
        login: LoginModule,
        dashboard: DashboardModule
    },
    signals: {
        defaultRouted: redirect('overview/analyses/')
    }
})
