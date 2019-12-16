import tippy from 'tippy.js'
import copy from 'copy-to-clipboard'
import toastr from 'toastr'
import 'tippy.js/dist/tippy.css'

import app from '../ng-decorators'

const copyOnClick = {
    name: 'copyOnClick',
    defaultValue: false,

    fn: (instance) => {
        const copyClickHandler = (event) => {
            copy(instance.props.content)
            toastr.info('Copied text to clipboard')
        }
        return {
            onMount(instance) {
                if (instance.props.copyOnClick) {
                    instance.popperChildren.content.classList.add('clipboard')
                    instance.popperChildren.content.addEventListener('click', copyClickHandler)
                }
            },
            onHidden(instance) {
                instance.popperChildren.content.removeEventListener('click', copyClickHandler)
            }
        }
    }
}

tippy.setDefaultProps({
    theme: 'la',
    delay: [500, 200],
    plugins: [copyOnClick]
})

app.directive('tippyTitle', function() {
    return {
        restrict: 'A',
        link: ($scope, elem, attrs) => {
            const enableCopy = attrs.tippyClipboard === 'true'
            const instance = tippy(elem[0], {
                interactive: enableCopy,
                copyOnClick: enableCopy
            })
            attrs.$observe('tippyTitle', (c) => {
                instance.setContent(c)
            })
        }
    }
})

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
                        const toCompile = `<div class="tippy-popover">${title}<div ng-include="'${attrs.tippyPopover}'"></div></div>`
                        const compiled = $compile(toCompile)($scope)[0]
                        instance.setContent(compiled)
                        $scope.$apply()
                    }
                }

                const instance = tippy(elem[0], props)
                attrs.$observe('tippyPlacement', (c) => {
                    instance.setProps({ placement: c })
                })

                attrs.$observe('tippyTrigger', (c) => {
                    instance.setProps({ trigger: c })
                })
            }
        }
    }
])
