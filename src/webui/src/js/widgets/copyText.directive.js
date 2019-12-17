import copy from 'copy-to-clipboard'
import toastr from 'toastr'

import app from '../ng-decorators'

app.directive('copyText', function() {
    return {
        restrict: 'E',
        scope: {
            text: '@'
        },
        template: `<div class="copy-text" ng-click="copyText(); $event.preventDefault();">{{text}}</div>`,
        controller: [
            '$scope',
            ($scope) => {
                $scope.copyText = () => {
                    copy($scope.text)
                    toastr.info('Copied text to clipboard')
                }
            }
        ]
    }
})
