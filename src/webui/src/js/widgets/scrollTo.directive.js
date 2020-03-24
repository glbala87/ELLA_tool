import app from '../ng-decorators'

app.directive('scrollTo', function() {
    return {
        restrict: 'A',
        link: (scope, elem, attrs) => {
            const getScrollFunc = (elem) => {
                if (attrs.scrollPosition === 'top') {
                    return () => elem.scrollIntoView(true)
                } else if (attrs.scrollPosition === 'view') {
                    return () => elem.scrollIntoView()
                } else {
                    // Default to scrollIntoView
                    return () => elem.scrollIntoView()
                }
            }
            if (attrs.scrollOnChange !== undefined) {
                attrs.$observe('scrollOnChange', () => {
                    setTimeout(() => getScrollFunc(elem[0])())
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
