import app from '../ng-decorators'

app.directive('scrollIntoView', function() {
    return {
        restrict: 'A',
        link: (scope, elem, attrs) => {
            const getScrollFunc = (elem) => {
                if (attrs.scrollFunction === 'scrollTo') {
                    return () => elem.scrollTo({ top: 0, left: 0 })
                } else {
                    return () => elem.scrollIntoView()
                }
            }
            if (attrs.scrollOnChange !== undefined) {
                attrs.$observe('scrollOnChange', () => {
                    getScrollFunc(elem[0])()
                })
            } else {
                // Auto scroll upon creation
                setTimeout(() => {
                    getScrollFunc(elem[0])()
                }, 500)
            }
        }
    }
})
