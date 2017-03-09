/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

/**
 <contentbox>
 A content box element with vertical header
 */
@Directive({
    selector: 'contentbox',
    scope: {
        color: '@',
        title: '@?', // Title (can also be set through options, options takes precedence)
        titleUrl: '@?',
        disabled: '=?',
    },
    transclude: { cbbody: 'cbbody' },
    templateUrl: 'ngtmpl/contentbox.ngtmpl.html'
})
@Inject('$scope')
export class ContentboxController {

    constructor($scope) {
        // textareas that are hidden won't automatically be resized when unhidden (http://www.jacklmoore.com/autosize/#faq-hidden)
        $scope.$watch( () => this.disabled, (_new, _old) => {
            if (_new == false) {
              setTimeout(() => {
                updateTextAreas();
              }, 100);
            }

            function updateTextAreas() {
                let comments = document.getElementsByClassName("id-autosizeable");
                for (let c of comments) {
                    autosize.update(c);
                }
            }
        });

    }

    getClasses() {
        let color = this.color ? this.color : "blue";
        let disabled = this.disabled ? "no-content" : "";
        return `${color} ${disabled}`;
    }
}
