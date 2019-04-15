import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import template from './modal.ngtmpl.html'

app.component('modal', {
    bindings: {
        showPath: '=',
        outsideClickPath: '=?' // If given, run signal when clicking outside
    },
    templateUrl: 'modal.ngtmpl.html',
    transclude: true,
    controller: connect(
        {
            show: state`${props`showPath`}`,
            outsideClick: signal`${props`outsideClickPath`}`
        },
        'Modal',
        ['$scope', ($scope) => {}]
    )
})
