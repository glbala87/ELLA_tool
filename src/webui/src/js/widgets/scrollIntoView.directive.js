import app from '../ng-decorators'

app.directive('scrollIntoView', function() {
    return {
        restrict: 'A',
        link: (scope, elem) => {
            setTimeout(() => {
                elem[0].scrollIntoView()
            }, 500)
        }
    }
})
