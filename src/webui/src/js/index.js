/* jshint esnext: true */

// Support for Object.entries. See https://www.npmjs.com/package/core-js
require('core-js/fn/object/entries');
require('core-js/fn/object/keys');
require('core-js/fn/object/values');
require('core-js/fn/array/includes');

// We must import all the modules using Angular for them to register
// although we're not using them explicitly.

import "./modals/addExcludedAllelesModal.service";
import "./modals/alleleAssessmentModal.service";
import "./modals/customAnnotationModal.service";
import "./modals/referenceEvalModal.service";
import "./modals/interpretationOverrideModal.service";
import './services/resources/acmgClassificationResource.service';
import './services/resources/alleleResource.service';
import './services/resources/alleleAssessmentResource.service';
import './services/resources/customAnnotationResource.service';
import './services/resources/analysisResource.service';
import './services/resources/interpretationResource.service';
import './services/resources/ReferenceResource.service';
import './services/resources/searchResource.service';
import "./services/allele.service";
import "./services/user.service";
import './services/ConfigService';
import './services/alleleFilter.service';
import './services/analysis.service';
import './services/interpretation.service';
import './services/search.service';
import './services/sidebar.service';
import './services/navbar.service';
import './filters';

import './views/analysis/analysis.directive';
import './views/analysis/analysisSelection.directive';
import './views/analysis/interpretationSingleSample.directive';
import './views/main.directive';
import './views/login.directive';
import './views/sidebar.directive';
import './views/navbar.directive';

import './widgets/annotationWidget.directive';
import './widgets/acmgSelection.directive';
import './widgets/analysisList.directive';
import './widgets/genomeBrowserWidget.directive';
import './widgets/frequencyDetailsWidget.directive';
import './widgets/transcriptWrapper.directive';
import './widgets/aclip.directive.js';
import './widgets/acmg.directive';
import './widgets/checkablebutton.directive';
import './widgets/autosizeTextarea.directive';
import './widgets/search.directive';
import './widgets/searchResults.directive';
import './widgets/card.directive';
import './widgets/interpretationbutton.directive';
import './widgets/allelecard/allelecard.directive';
import './widgets/allelecard/frequencysection.directive';
import './widgets/allelecard/externalsection.directive';
import './widgets/allelecard/predictionsection.directive';
import './widgets/allelecard/referencesection.directive';
import './widgets/allelecard/vardbsection.directive';
import './widgets/allelecard/classificationsection.directive';
import './widgets/reportcard/reportcard.directive';
import './widgets/isolateclick.directive';
import './widgets/genepanelvalue.directive';




import {Config, Inject, Run} from './ng-decorators';


class AppConfig {

    @Config()
    @Inject('$urlRouterProvider', '$stateProvider', '$resourceProvider', '$locationProvider')
    configFactory($urlRouterProvider, $stateProvider, $resourceProvider, $locationProvider) {
        $stateProvider.state('app', {
                views: {
                    app: {
                        template: '<main></main>'
                    }
                },
                resolve: {
                    // Preload global config before app starts
                    config: ['Config', (Config) => {
                        return Config.loadConfig();
                    }]
                }
            })
            .state('app.analyses', {
                url: '/analyses',
                views: {
                    content: {
                        template: '<analysis-selection></analysis-selection>'
                    }
                }
            })
            .state('app.interpretation', {
                url: '/analyses/:analysisId',
                views: {
                    content: {
                        template: '<analysis analysis-id="{{analysisId}}"></analysis>',
                        controller: ['$scope', '$stateParams', function($scope, $stateParams) {
                            $scope.analysisId = $stateParams.analysisId;
                        }]
                    }
                }
            })
            .state('login', {
                url: '/login',
                views: {
                    app: {
                        template: '<login></login>'
                    }
                }
            });

        // when there is an empty route, redirect to /analyses
        $urlRouterProvider.otherwise('/analyses');
        $locationProvider.html5Mode(true);
        $resourceProvider.defaults.stripTrailingSlashes = false;
    }

    @Run()
    @Inject('$rootScope', '$location', 'User')
    run($rootScope, $location, User) {
        // Redirect to login if no user is selected
        $rootScope.$on('$stateChangeStart', (event, toState, toParams) => {
            if (!User.getCurrentUserId()) {
                $location.path('/login');
            }
        });
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
