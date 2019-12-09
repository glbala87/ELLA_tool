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
        link: ($scope, elem) => {
            const enableCopy = $scope.tippyClipboard === 'true'
            if ($scope.tippyTitle && $scope.tippyTitle !== '') {
                tippy(elem[0], {
                    content: $scope.tippyTitle,
                    interactive: enableCopy,
                    copyOnClick: enableCopy
                })
            }
        },
        scope: {
            tippyTitle: '@',
            tippyClipboard: '@?'
        }
    }
})

app.directive('tippyPopover', function() {
    return {
        restrict: 'A',
        link: ($scope, elem) => {
            const toCompile = `<div><div ng-include="'${$scope.tippyPopover}'"></div></div>`
            const compiled = $scope.$compile(toCompile)($scope.$parent)[0]
            tippy(elem[0], {
                trigger: 'click',
                content: () => compiled,
                allowHTML: true,
                delay: 0,
                flipOnUpdate: true,
                maxWidth: '120rem',
                boundary: 'window',
                interactive: true,
                appendTo: document.body,
                placement: $scope.tippyPlacement ? $scope.tippyPlacement : 'top'
            })
        },
        controller: [
            '$compile',
            '$scope',
            ($compile, $scope) => {
                $scope.$compile = $compile
            }
        ],
        scope: {
            tippyPopover: '<',
            tippyPlacement: '@?'
        }
    }
})
