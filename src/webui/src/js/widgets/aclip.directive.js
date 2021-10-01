/* jshint esnext: true */
import toastr from 'toastr'
import copy from 'copy-to-clipboard'
import app from '../ng-decorators'
import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import { connect } from '@cerebral/angularjs'

/**
 * Directive for supporting dynamically switching between normal
 * <a> open link behavior and copy-link-to-clipboard instead.
 */

app.component('aClip', {
    bindings: {
        href: '@?',
        title: '@?',
        toClipboard: '=?',
        linkText: '@?'
    },
    transclude: true,
    template: `<span><a title="{{$ctrl.title}}" ng-if="::!$ctrl.shouldCopy()" ng-href="{{$ctrl.href}}" target="{{$ctrl.href}}" ng-transclude></a><a style="cursor: pointer;" ng-if="::$ctrl.shouldCopy()" title="{{$ctrl.title}}" ng-click="$ctrl.copyToClipboard()" ng-transclude></a></span>`,
    controller: connect(
        {
            fallbackCopyToClipboard: state`app.config.app.links_to_clipboard`
        },
        'aClip',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    attrs: {
                        linkText: $ctrl.linkText
                    },
                    copyToClipboard() {
                        copy($ctrl.href)
                        toastr.info('Copied link to clipboard.', null, 1000)
                        console.log(`Copied ${$ctrl.href} to clipboard.`)
                    },
                    shouldCopy() {
                        return $ctrl.toClipboard !== undefined
                            ? $ctrl.toClipboard
                            : $ctrl.fallbackCopyToClipboard
                    }
                })
            }
        ]
    )
})
