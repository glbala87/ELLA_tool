/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

/**
 * Directive for supporting dynamically switching between normal
 * <a> open link behavior and copy-link-to-clipboard instead.
 * @type {String}
 */
@Directive({
    selector: 'a-clip',
    scope: {
        href: '@?',
        title: '@?',
        toClipboard: '=?'
    },
    transclude: true,
    template: `<span><a title="{{title}}" ng-if="::!vm.shouldCopy()" ng-href="{{vm.href}}" target="{{vm.href}}" ng-transclude></a><a style="cursor: pointer;" ng-if="::vm.shouldCopy()" title="{{title}}" ng-click="vm.copyToClipboard()" ng-transclude></a></span>`
})
@Inject('clipboard', 'Config', 'toastr')
export class HrefController {
    constructor(clipboard, Config, toastr) {
        this.clipboard = clipboard
        this.config = Config.getConfig()
        this.toastr = toastr
    }

    copyToClipboard() {
        this.clipboard.copyText(this.href)
        this.toastr.info('Copied link to clipboard.', null, 1000)
        console.log(`Copied ${this.href} to clipboard.`)
    }

    shouldCopy() {
        if (this.toClipboard === undefined) {
            return this.config.app.links_to_clipboard
        }
        return this.toClipboard === 'true'
    }
}
