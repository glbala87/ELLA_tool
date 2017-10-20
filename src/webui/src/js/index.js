/* jshint esnext: true */

// Support for Object.entries. See https://www.npmjs.com/package/core-js
require('core-js/fn/object/entries');
require('core-js/fn/object/keys');
require('core-js/fn/object/values');
require('core-js/fn/array/includes');

// We must import all the modules using Angular for them to register
// although we're not using them explicitly.

import "./modals/addExcludedAllelesModal.service";
import "./modals/alleleAssessmentHistoryModal.service";
import "./modals/customAnnotationModal.service";
import "./modals/annotateVCFFileModal.service";
import "./modals/referenceEvalModal.service";
import "./modals/interpretationOverrideModal.service";
import "./modals/igvModal.service";
import './services/resources/acmgClassificationResource.service';
import './services/resources/alleleResource.service';
import './services/resources/alleleAssessmentResource.service';
import './services/resources/customAnnotationResource.service';
import './services/resources/genepanelResource.service';
import './services/resources/analysisResource.service';
import './services/resources/interpretationResource.service';
import './services/resources/ReferenceResource.service';
import './services/resources/searchResource.service';
import './services/resources/genepanelResource.service';
import './services/resources/annotationjobResource.service';
import './services/resources/finalizationResource.service';
import './services/resources/overviewResource.service';
import './services/resources/workflowResource.service';
import './services/resources/loginResource.service';
import './services/resources/attachmentResource.service';
import "./services/allele.service";
import "./services/user.service";
import './services/ConfigService';
import './services/alleleFilter.service';
import './services/analysis.service';
import './services/workflow.service';
import './services/search.service';
import './services/sidebar.service';
import './services/navbar.service';
import './filters';

import './views/workflow/workflowAnalysis.directive';
import './views/workflow/workflowAllele.directive';
import './views/workflow/interpretation.directive';
import './views/overviews/analysisSelection.directive';
import './views/overviews/alleleSelection.directive';
import './views/userDashboard.directive';
import './views/main.directive';
import './views/overview.directive';
import './views/login.directive';
import './views/sidebar.directive';
import './views/alleleSidebar.directive';
import './views/navbar.directive';

import './widgets/alleleinfo/alleleInfoAcmgSelection.directive';
import './widgets/alleleinfo/alleleInfoQuality.directive';
import './widgets/alleleinfo/alleleInfoConsequence.directive';
import './widgets/alleleinfo/alleleInfoReferences.directive';
import './widgets/alleleinfo/alleleInfoSplice.directive';
import './widgets/alleleinfo/alleleInfoSplicePopoverContent.directive';
import './widgets/alleleinfo/alleleInfoPredictionOther.directive';
import './widgets/alleleinfo/alleleInfoFrequencyExac.directive';
import './widgets/alleleinfo/alleleInfoFrequencyGnomadGenomes.directive';
import './widgets/alleleinfo/alleleInfoFrequencyGnomadExomes.directive';
import './widgets/alleleinfo/alleleInfoFrequency1000g.directive';
import './widgets/alleleinfo/alleleInfoFrequencyEsp6500.directive';
import './widgets/alleleinfo/alleleInfoFrequencyIndb.directive';
import './widgets/alleleinfo/alleleInfoDbsnp.directive';
import './widgets/alleleinfo/alleleInfoHgmd.directive';
import './widgets/alleleinfo/alleleInfoClinvar.directive';
import './widgets/alleleinfo/alleleInfoExternalOther.directive';
import './widgets/alleleinfo/alleleInfoVardb.directive';

import './widgets/analysisList.directive';
import './widgets/alleleAssessment.directive';
import './widgets/alleleList.directive';
import './widgets/allelebar.directive';
import './widgets/attachment.directive';
import './widgets/genomeBrowserWidget.directive';
import './widgets/frequencyDetailsWidget.directive';
import './widgets/repeatWrapper.directive';
import './widgets/aclip.directive.js';
import './widgets/acmg.directive';
import './widgets/checkablebutton.directive';
import './widgets/autosizeTextarea.directive';
import './widgets/contentbox.directive';
import './widgets/sectionbox.directive';
import './widgets/search.directive';
import './widgets/searchModule.directive';
import './widgets/workflowButtons.directive';
import './widgets/allelesectionbox/allelesectionbox.directive';
import './widgets/allelesectionbox/allelesectionboxcontent.directive';
import './widgets/allelesectionbox/upload.directive';
import './widgets/reportcard/reportcard.directive';
import './widgets/isolateclick.directive';
import './widgets/genepanelvalue/genepanelvalue.directive.js';
import './widgets/igv.directive.js';
import './widgets/wysiwygjsEditor.directive';
import './widgets/referenceAssessment.directive';

import {Config, Inject, Run} from './ng-decorators';

class AppConfig {

    @Config()
    @Inject('$urlRouterProvider', '$stateProvider', '$resourceProvider', '$locationProvider')
    configFactory($urlRouterProvider, $stateProvider, $resourceProvider, $locationProvider) {
        $stateProvider.state('app', {
                abstract: true,
                resolve: {
                    // Preload global config before app starts
                    config: ['Config', (Config) => {
                        return Config.loadConfig();
                    }]
                }
            })
            .state('app.main', {
                abstract: true,
                views: {
                    'app@': {  // https://github.com/angular-ui/ui-router/wiki/Multiple-Named-Views#view-names---relative-vs-absolute-names
                        template: '<main></main>'
                    }
                }
            })
            .state('app.main.analyses', {
                url: '/overview/:view',
                views: {
                    'content': {
                        template: '<overview selected-view="selectedView"></overview>',
                        controller: ['$scope', '$stateParams', 'Config', function($scope, $stateParams, Config) {
                            $scope.selectedView = $stateParams.view || localStorage.getItem("overview") || "analyses";
                        }]
                    }
                }
            })
            .state('app.main.analysisinterpretation', {
                url: '/analyses/:analysisId',
                views: {
                    'content': {
                        template: '<workflow-analysis analysis-id="{{analysisId}}"></workflow-analysis>',
                        controller: ['$scope', '$stateParams', '$location', function($scope, $stateParams, $location) {
                            $scope.analysisId = $stateParams.analysisId;
                        }]
                    }
                }
            })
            .state('app.main.variantinterpretation', {
                url: '/variants/{reference_genome}/{variant_selector}?gp_name&gp_version',
                views: {
                    'content': {
                        template: '<workflow-allele reference-genome="{{reference_genome}}" variant-selector="{{variant_selector}}" genepanel-name="{{gp_name}}" genepanel-version="{{gp_version}}"></workflow-allele>',
                        controller: ['$scope', '$stateParams', function($scope, $stateParams) {
                            $scope.reference_genome = $stateParams.reference_genome;
                            $scope.variant_selector = $stateParams.variant_selector;
                            $scope.gp_name = $stateParams.gp_name;
                            $scope.gp_version = $stateParams.gp_version;
                        }]
                    }
                }
            })
            .state('app.main.dashboard', {
                url: '/dashboard',
                views: {
                    'content': {
                        template: '<user-dashboard></user-dashboard>'
                    }
                }
            })
            .state('app.login', {
                url: '/login',
                views: {
                    'app@': {
                        template: '<login></login>'
                    }
                }
            });

        // when there is an empty route, redirect to /analyses
        $urlRouterProvider.otherwise('/overview/');
        $locationProvider.html5Mode(true);
        $resourceProvider.defaults.stripTrailingSlashes = false;
    }

    @Run()
    @Inject('$rootScope', '$location', 'User')
    run($rootScope, $location, User) {
        // Redirect to login if no user is logged in
        $rootScope.$on('$stateChangeStart', (event, toState, toParams) => {
            if (!User.hasUser()) {
                console.log("Did not find user, trying to load...")
                User.loadUser().catch( () => {
                    console.log("Did not load user, redirecting...")
                    $location.path('/login');
                    }
                )}
        })
    }
}


// Alias Angular's $q implementation to 'Promise' so that we can keep our code ES6
// compliant. We need this as the $q keep issues digest cycles automatically.
// This has some limitations, however, as the interfaces are not entirely equal.
Promise = function (resolver) {
    return angular.element(document.body).injector().get('$q')(resolver);
};

Promise.all = function() {
    let temp = angular.element(document.body).injector().get('$q').all.apply(this, arguments);
    temp.spread = (func) => {
        return temp.then(value => {
            return func.apply(this, value);
        });
    };
    return temp;
};



// Sets up general event handlers for drag and drop events on the window and body
window.onload = () => {
    // Prevent default behaviour of drag and drop of files
    window.addEventListener("dragover", function (e) {
        e = e || event;
        e.preventDefault();
    }, false);
    window.addEventListener("drop", function (e) {
        e = e || event;
        e.preventDefault();
    }, false);

    // This seems very hackish
    // Purpose: Keep track of whether or not a file is currently being dragged
    // Increment on dragenter, decrease on dragleave
    // A positive value indicates that a file is currently being dragged
    let body = document.body;
    body.dragCount = 0;


    let events = ["dragleave", "dragenter", "drop"]
    for (let event of events) {
        body.addEventListener(event, function (e) {
            if (e.dataTransfer.types.indexOf('Files') < 0) return; // Elements other than files being dragged
            if (e.type === "dragenter") {
                this.dragCount++;
            } else if (e.type === "dragleave") {
                this.dragCount--;
            } else if (e.type === "drop") {
                this.dragCount = 0;
            }

            // Hide/show droparea elements based on dragcount value
            let dropAreas = document.getElementsByClassName("droparea")
            for (let dropArea of dropAreas) {
                if (this.dragCount > 0) {
                    dropArea.classList.remove("droparea-hidden")
                } else {
                    dropArea.classList.add("droparea-hidden")
                }
            }

            e.preventDefault();
        }, false);
    }
}
