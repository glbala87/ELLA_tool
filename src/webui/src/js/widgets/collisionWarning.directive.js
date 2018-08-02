import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './collisionWarning.ngtmpl.html'

app.component('collisionWarning', {
    templateUrl: 'collisionWarning.ngtmpl.html',
    controller: connect(
        {
            type: state`views.workflows.type`,
            collisions: state`views.workflows.data.collisions`
        },
        'CollisionWarning',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($scope.$ctrl, {
                    getTitle() {
                        let title = ''
                        if ($ctrl.collisions) {
                            if ($ctrl.type === 'allele') {
                                title += `This variant is currently being worked on `
                                if ($ctrl.collisions.length === 1) {
                                    title += 'in another workflow.'
                                } else {
                                    title += 'in other workflows.'
                                }
                            } else if ($ctrl.type === 'analysis') {
                                title = 'There '
                                if ($ctrl.collisions.length > 1) {
                                    title += `are currently ${
                                        $ctrl.collisions.length
                                    } variants being worked on in other workflows.`
                                } else {
                                    title += `is currently ${
                                        $ctrl.collisions.length
                                    } variant being worked on in another workflow.`
                                }
                            }
                        }
                        return title
                    },
                    getCollisionText(collision) {
                        let text = ''
                        if ($ctrl.type === 'allele') {
                            text += `${collision.type === 'analysis' ? 'Analysis' : 'Variant'}`
                            text += ` ${
                                collision.user ? 'by ' + collision.user.full_name : 'in review'
                            }`
                        } else if ($ctrl.type === 'analysis') {
                            text += `${collision.allele.formatted.display}`
                            text += ` ${
                                collision.user
                                    ? ' is worked on by ' + collision.user.full_name
                                    : 'is pending review'
                            } ${
                                collision.type === 'analysis'
                                    ? 'as part of an analysis'
                                    : 'in variant workflow'
                            }`
                        }
                        return text
                    }
                })
            }
        ]
    )
})
