/* jshint esnext: true */
import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'

import template from './sectionbox.ngtmpl.html' // eslint-disable-line no-unused-vars

// /**
//  <sectionbox>
//  A section box element with vertical header
//  */

app.component('sectionbox', {
    bindings: {
        ngDisabled: '=?',
        modal: '=?', // bool: whether sectionbox is part of a modal
        topcontrols: '=?', // bool: whether controls should live at the top of the section
        collapsible: '=?', // bool: whether box can collapse
        collapsed: '=?',
        onCollapse: '&?',
        onClose: '&?',
        color: '@'
    },
    transclude: {
        title: 'maintitle',
        subtitle: '?subtitle',
        contentwrapper: '?contentwrapper',
        top: '?top',
        controls: '?controls'
    },
    templateUrl: 'sectionbox.ngtmpl.html',
    controller: connect(
        {},
        'sectionbox',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                console.log($ctrl.controls)
                Object.assign($ctrl, {
                    getClasses() {
                        let color = this.color ? this.color : 'blue'
                        let collapsed = this.getCollapseStatus() ? 'collapsed' : ''
                        return `${color} ${collapsed}`
                    },

                    getCollapseStatus() {
                        return this.collapsed
                    },

                    collapse() {
                        if (this.isModal() || !this.isCollapsible()) {
                            return
                        }
                        this.collapsed = !this.getCollapseStatus()
                        if (this.onCollapse) {
                            this.onCollapse({ collapsed: this.collapsed })
                        }
                    },
                    isCollapsible() {
                        return (
                            (this.collapsible === undefined || this.collapsible) && !this.isModal()
                        )
                    },

                    isModal() {
                        return this.modal != undefined || this.modal === true
                    },

                    onTop() {
                        return this.topcontrols != undefined || this.topcontrols === true
                    },

                    close() {
                        this.onClose()()
                    }
                })
            }
        ]
    )
})
