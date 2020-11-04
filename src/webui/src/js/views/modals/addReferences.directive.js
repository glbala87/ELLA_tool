/* jshint esnext: true */
import app from '../../ng-decorators'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { signal, state } from 'cerebral/tags'
import template from './addReferences.ngtmpl.html'

const userReferences = Compute(
    state`views.workflows.modals.addReferences.userReferenceIds`,
    state`views.workflows.modals.addReferences.data.references`,
    (userReferenceIds, references) => {
        if (!userReferenceIds || !references) {
            return {}
        }
        const userReferences = {}
        for (let refId of userReferenceIds) {
            userReferences[refId] = references[refId]
        }
        return userReferences
    }
)

app.component('addReferences', {
    templateUrl: 'addReferences.ngtmpl.html',
    controller: connect(
        {
            alleleId: state`views.workflows.modals.addReferences.alleleId`,
            referenceMode: state`views.workflows.modals.addReferences.referenceMode`,
            referenceModes: state`views.workflows.modals.addReferences.referenceModes`,
            annotationGroups: state`views.workflows.modals.addReferences.annotationGroups`,
            currentSelection: state`views.workflows.modals.addReferences.selection`,
            maxSearchResults: state`views.workflows.modals.addReferences.maxSearchResults`,
            userReferenceIds: state`views.workflows.modals.addReferences.userReferenceIds`,
            userReferences,
            dismissClicked: signal`views.workflows.modals.addReferences.dismissClicked`,
            selectionChanged: signal`views.workflows.modals.addReferences.selectionChanged`,
            saveClicked: signal`views.workflows.modals.addReferences.saveClicked`,
            addReference: signal`views.workflows.modals.addReferences.addReference`,
            removeReference: signal`views.workflows.modals.addReferences.removeReference`
        },
        'addReferences',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                $ctrl.modelManual = {}
                $ctrl.manualReferenceInputs = {
                    Published: [
                        {
                            key: 'authors',
                            left: 'Authors',
                            placeholder: 'Authors*'
                        },
                        {
                            key: 'title',
                            left: 'Title',
                            placeholder: 'Title*'
                        },
                        {
                            key: 'journal',
                            left: 'Journal / Book',
                            placeholder: 'Journal/book*'
                        },
                        {
                            key: 'volume',
                            left: 'Volume',
                            placeholder: 'Volume'
                        },
                        {
                            key: 'issue',
                            left: 'Issue',
                            placeholder: 'Issue'
                        },
                        {
                            key: 'year',
                            left: 'Year',
                            placeholder: 'Year*'
                        },
                        {
                            key: 'pages',
                            left: 'Pages',
                            placeholder: 'Pages'
                        },
                        {
                            key: 'abstract',
                            left: 'Abstract',
                            placeholder: 'Abstract'
                        }
                    ],
                    Unpublished: [
                        {
                            key: 'authors',
                            left: 'Authors',
                            placeholder: 'Authors/responsible*'
                        },
                        {
                            key: 'title',
                            left: 'Title',
                            placeholder: 'Title/short description*'
                        },
                        {
                            key: 'journal',
                            left: 'Place',
                            placeholder: 'Place of study*'
                        },
                        {
                            key: 'year',
                            left: 'Year',
                            placeholder: 'Year*'
                        },
                        {
                            key: 'abstract',
                            left: 'Abstract',
                            placeholder: 'Abstract'
                        }
                    ]
                }
                Object.assign($ctrl, {
                    canAddManualReference: () => {
                        return !(
                            $ctrl.currentSelection.title &&
                            $ctrl.currentSelection.authors &&
                            $ctrl.currentSelection.journal &&
                            $ctrl.currentSelection.year
                        )
                    }
                })
            }
        ]
    )
})
