import '../css/base.css'
import '../sass/main.scss'

// Import here for template handling to be injected correctly
import angular from 'angular'

// We must import all the modules using Angular for them to register
// although we're not using them explicitly.

import './modals/alleleAssessmentHistoryModal.service'
import './modals/customAnnotationModal.service'
import './modals/referenceEvalModal.service'
import './modals/igvModal.service'
// Legacy: Some modals are not ported to Cerebral yet,
// and these resources are therefore still in use
import './services/resources/alleleAssessmentResource.service'
import './services/resources/customAnnotationResource.service'
import './services/resources/analysisResource.service'
import './services/resources/ReferenceResource.service'
import './services/resources/attachmentResource.service'
import './services/user.service'
import './services/ConfigService'
import './filters'

import './views/modals/finishConfirmation.directive'
import './views/modals/showAnalysesForAllele.directive'
import './views/modals/addExcludedAlleles.directive'
import './views/modals/reassignWorkflow.directive'
import './views/modals/genepanelOverview.directive'
import './views/workflow/workflow.directive'
import './views/workflow/workflowLoading.directive'
import './views/workflow/interpretation.directive'
import './views/overviews/analysisSelection.directive'
import './views/overviews/alleleSelection.directive'
import './views/overviews/import.directive'
import './views/overviews/customGenepanelEditor.directive'
import './views/userDashboard.directive'
import './views/main.directive'
import './views/modal.directive'
import './views/overview.directive'
import './views/overviewNavbar.directive'
import './views/login.directive'
import './views/alleleSidebar.directive'
import './views/alleleSidebarList.directive'
import './views/navbar.directive'
import './views/visualization.directive'

import './widgets/alleleinfo/alleleInfoAcmgSelection.directive'
import './widgets/alleleinfo/alleleInfoQuality.directive'
import './widgets/alleleinfo/alleleInfoConsequence.directive'
import './widgets/alleleinfo/alleleInfoReferences.directive'
import './widgets/alleleinfo/alleleInfoReferenceDetail.directive'
import './widgets/alleleinfo/alleleInfoPredictionOther.directive'
import './widgets/alleleinfo/alleleInfoFrequencyExac.directive'
import './widgets/alleleinfo/alleleInfoFrequencyGnomadGenomes.directive'
import './widgets/alleleinfo/alleleInfoFrequencyGnomadExomes.directive'
import './widgets/alleleinfo/alleleInfoFrequencyIndb.directive'
import './widgets/alleleinfo/alleleInfoDbsnp.directive'
import './widgets/alleleinfo/alleleInfoHgmd.directive'
import './widgets/alleleinfo/alleleInfoClinvar.directive'
import './widgets/alleleinfo/alleleInfoExternalOther.directive'
import './widgets/alleleinfo/alleleInfoVardb.directive'
import './widgets/annotationimport/importSingle.directive'

import './widgets/markdownIt.directive'
import './widgets/scrollIntoView.directive'
import './widgets/collisionWarning.directive'
import './widgets/alleleWarning.directive'
import './widgets/analysisList.directive'
import './widgets/alleleAssessment.directive'
import './widgets/alleleList.directive'
import './widgets/importList.directive'
import './widgets/interpretationRoundInfo.directive'
import './widgets/allelebar.directive'
import './widgets/allelebar/workflowInterpretationRounds.directive'
import './widgets/attachment.directive'
import './widgets/frequencyDetailsWidget.directive'
import './widgets/aclip.directive.js'
import './widgets/acmg.directive'
import './widgets/checkablebutton.directive'
import './widgets/autosizeTextarea.directive'
import './widgets/contentbox.directive'
import './widgets/sectionbox.directive'
import './widgets/searchModule.directive'
import './widgets/workflowButtons.directive'
import './widgets/allelesectionbox/allelesectionbox.directive'
import './widgets/allelesectionbox/allelesectionboxcontent.directive'
import './widgets/allelesectionbox/upload.directive'
import './widgets/reportcard/reportcard.directive'
import './widgets/isolateclick.directive'
import './widgets/genepanelvalue/genepanelvalue.directive.js'
import './widgets/igv.directive.js'
import './widgets/wysiwygjsEditor.directive'
import './widgets/referenceAssessment.directive'
import './widgets/analysisInfo.directive'
import './widgets/workflowbar.directive'
import './widgets/interpretationLog.directive'
import './widgets/interpretationLogItem.directive'

import Devtools from 'cerebral/devtools'
import RootModule from './store/modules'
import { Config, Inject, Run } from './ng-decorators'

class AppConfig {
    @Config()
    @Inject(
        '$injector',
        'cerebralProvider',
        '$resourceProvider',
        '$compileProvider',
        '$provide',
        '$locationProvider'
    )
    configFactory(
        $injector,
        cerebralProvider,
        $resourceProvider,
        $compileProvider,
        $provide,
        $locationProvider
    ) {
        let config = {
            devtools: Devtools({
                host: 'localhost:8585',
                bigComponentsWarning: 50, // Our AngularJS components are traditionally very large
                reconnect: false // Can be annoying when devtools not open
            })
        }
        // DEV: Comment out line below to activate devtools
        // (impacts performance even without debugger running)
        config.devtools = null

        cerebralProvider.configure(RootModule(), config)

        // Needed after upgrade to Angular >1.5,
        // since we haven't migrated to using $onInit()
        $compileProvider.preAssignBindingsEnabled(true)
        $compileProvider.debugInfoEnabled(true)
        $compileProvider.commentDirectivesEnabled(true)
        $compileProvider.cssClassDirectivesEnabled(true)

        // Hack disabling Angular's watch of url.
        // Leads to infinite digest when changing url using cerebral (or any history.pushState API)
        $provide.decorator('$location', [
            '$delegate',
            '$browser',
            function($delegate, $browser) {
                $delegate.absUrl = function() {
                    return $browser.url()
                }
                return $delegate
            }
        ])

        $locationProvider.html5Mode({
            enabled: true,
            rewriteLinks: false
        })
        $resourceProvider.defaults.stripTrailingSlashes = false
    }
}

// Alias Angular's $q implementation to 'Promise' so that we can keep our code ES6
// compliant. We need this as the $q keep issues digest cycles automatically.
// This has some limitations, however, as the interfaces are not entirely equal.
let org_promise = Promise
Promise = function(resolver) {
    try {
        return angular
            .element(document.body)
            .injector()
            .get('$q')(resolver)
    } catch (e) {
        // Before angular is loaded, return normal Promise implementation
        // Needed for cerebral to function
        return new org_promise(resolver)
    }
}

Promise.resolve = function(val) {
    try {
        return angular
            .element(document.body)
            .injector()
            .get('$q')(resolver)
            .resolve(val)
    } catch (e) {
        return org_promise.resolve(val)
    }
}

Promise.all = function() {
    let temp = angular
        .element(document.body)
        .injector()
        .get('$q')
        .all.apply(this, arguments)
    temp.spread = (func) => {
        return temp.then((value) => {
            return func.apply(this, value)
        })
    }
    return temp
}

// Sets up general event handlers for drag and drop events on the window and body
window.onload = () => {
    // Prevent default behaviour of drag and drop of files
    window.addEventListener(
        'dragover',
        function(e) {
            e = e || event
            e.preventDefault()
        },
        false
    )
    window.addEventListener(
        'drop',
        function(e) {
            e = e || event
            e.preventDefault()
        },
        false
    )

    // This seems very hackish
    // Purpose: Keep track of whether or not a file is currently being dragged
    // Increment on dragenter, decrease on dragleave
    // A positive value indicates that a file is currently being dragged
    let body = document.body
    body.dragCount = 0

    let events = ['dragleave', 'dragenter', 'drop']
    for (let event of events) {
        body.addEventListener(
            event,
            function(e) {
                if (e.dataTransfer.types.indexOf('Files') < 0) return // Elements other than files being dragged
                if (e.type === 'dragenter') {
                    this.dragCount++
                } else if (e.type === 'dragleave') {
                    this.dragCount--
                } else if (e.type === 'drop') {
                    this.dragCount = 0
                }

                // Hide/show droparea elements based on dragcount value
                let dropAreas = document.getElementsByClassName('droparea')
                for (let dropArea of dropAreas) {
                    if (this.dragCount > 0) {
                        dropArea.classList.remove('droparea-hidden')
                    } else {
                        dropArea.classList.add('droparea-hidden')
                    }
                }

                e.preventDefault()
            },
            false
        )
    }
}
