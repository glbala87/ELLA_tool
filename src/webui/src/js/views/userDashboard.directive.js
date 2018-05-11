/* jshint esnext: true */


import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('userDashboard', {
    templateUrl: 'ngtmpl/userDashboard.ngtmpl.html',
    controller: connect(
        {
            logoutClicked: signal`views.dashboard.logoutClicked`,
            user: state`app.user`,
            usersInGroup: state`views.dashboard.data.usersInGroup`,
            userStats: state`views.dashboard.data.userStats`
        }
    )
})