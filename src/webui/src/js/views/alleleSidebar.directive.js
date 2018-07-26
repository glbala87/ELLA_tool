import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import template from './alleleSidebar.ngtmpl.html'

app.component('alleleSidebar', {
    templateUrl: 'alleleSidebar.ngtmpl.html',
    controller: connect(
        {},
        'AlleleSidebar'
    )
})
