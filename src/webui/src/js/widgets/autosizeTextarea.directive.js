/* jshint esnext: true */

import autosize from 'autosize'
import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'

app.component('autosizeTextarea', {
    bindings: {
        placeholder: '@?',
        ngModel: '=',
        ngModelWatch: '=?',
        ngDisabled: '=?',
        ngChange: '&?'
    },
    template:
        '<textarea class="id-autosizeable" ng-disabled="$ctrl.ngDisabled" rows=1 placeholder="{{$ctrl.placeholder}}" ng-model="$ctrl.ngModel" ng-model-watch="$ctrl.ngModelWatch"></textarea>',
    controller: connect(
        {},
        'autosizeTextarea',
        [
            '$scope',
            '$element',
            ($scope, $element) => {
                const $ctrl = $scope.$ctrl
                const textarea = $element.children()[0]
                autosize(textarea)
                $scope.$watch(
                    () => {
                        return $ctrl.ngModel
                    },
                    (n, o) => {
                        // ng-change in the template seems to run before ng-model has been set,
                        // therefore we need to run it here
                        // Do not trigger ngChange if new type is not yet defined
                        if ($ctrl.ngChange && n !== undefined) {
                            $ctrl.ngChange()
                        }
                        autosize(textarea)
                    }
                )

                // when textarea initially is hidden and then shown, we must explicitly autosize it:
                // (http://www.jacklmoore.com/autosize/#faq-hidden)
                setTimeout(() => {
                    autosize.update(textarea)
                }, 100)
            }
        ]
    )
})
