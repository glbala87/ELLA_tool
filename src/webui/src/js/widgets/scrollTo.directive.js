import app from '../ng-decorators'

app.directive('scrollTo', function() {
    return {
        restrict: 'A',
        link: (scope, elem, attrs) => {
            const getScrollFunc = (elem) => {
                if (attrs.scrollPosition === 'top') {
                    return () => elem.scrollTo({ top: 0, left: 0 })
                } else if (attrs.scrollPosition === 'view') {
                    return () =>
                        elem.scrollIntoView({
                            block: 'nearest'
                        })
                } else {
                    // Default to scrollIntoView
                    return () =>
                        elem.scrollIntoView({
                            block: 'nearest'
                        })
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
