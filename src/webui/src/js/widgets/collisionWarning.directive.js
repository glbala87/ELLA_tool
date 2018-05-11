import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('collisionWarning', {
    templateUrl: 'ngtmpl/collisionWarning.ngtmpl.html',
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
                                title += `This variant is currently `
                                if ($ctrl.collisions.length === 1) {
                                    title += `${
                                        $ctrl.collisions[0].user
                                            ? 'being worked on by ' +
                                              $ctrl.collisions[0].user.full_name
                                            : 'in review'
                                    } `
                                    title += 'in another workflow.'
                                } else {
                                    title += 'being worked on in other workflows.'
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
                            text += `${collision.allele.formatted.hgvsc ||
                                collision.allele.formatted.hgsvg}`
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
