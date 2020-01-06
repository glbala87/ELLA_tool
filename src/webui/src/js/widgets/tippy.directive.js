import tippy from 'tippy.js'
import copy from 'copy-to-clipboard'
import toastr from 'toastr'
import 'tippy.js/dist/tippy.css'

import app from '../ng-decorators'

tippy.setDefaultProps({
    theme: 'la',
    delay: [350, 200]
})

app.directive('tippyTitle', [
    '$compile',
    function($compile) {
        return {
            restrict: 'A',
            link: ($scope, elem, attrs) => {
                const enableCopy = attrs.tippyClipboard === 'true'
                const instance = tippy(elem[0], {
                    interactive: enableCopy
                })
                attrs.$observe('tippyTitle', (c) => {
                    if (enableCopy) {
                        const toCompile = `<copy-text text="${c}"></copy-text>`
                        c = $compile(toCompile)($scope)[0]
                    }
                    instance.setContent(c)
                })
            }
        }
    }
])

app.directive('tippyPopover', [
    '$compile',
    function($compile) {
        return {
            restrict: 'A',
            link: ($scope, elem, attrs) => {
                const props = {
                    trigger: attrs.tippyTrigger ? attrs.tippyPopover : 'click',
                    allowHTML: true,
                    delay: 0,
                    flipOnUpdate: true,
                    maxWidth: '120rem',
                    boundary: 'window',
                    interactive: true,
                    appendTo: document.body,
                    placement: attrs.tippyPlacement ? attrs.tippyPlacement : 'top',
                    onTrigger: (instance, event) => {
                        const title = attrs.tippyPopoverTitle
                            ? `<div class="tippy-popover-title">${attrs.tippyPopoverTitle}</div>`
                            : ''

                        let toCompile = ''
                        if (attrs.tippyPopover.endsWith('.html')) {
                            toCompile = `<div class="tippy-popover">${title}<div ng-include="'${attrs.tippyPopover}'"></div></div>`
                        } else {
                            toCompile = `<div class="tippy-popover">${title}<div>${attrs.tippyPopover}</div></div>`
                        }
                        const compiled = $compile(toCompile)($scope)[0]
                        instance.setContent(compiled)
                        $scope.$apply()
                    }
                }

                tippy(elem[0], props)
            }
        }
    }
])
