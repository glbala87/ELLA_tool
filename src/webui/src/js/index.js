/* jshint esnext: true */

// Support for Object.entries. See https://www.npmjs.com/package/core-js
require('core-js/fn/object/entries');

// We must import all the modules using Angular for them to register
// although we're not using them explicitly.

import "./modals/addExcludedAllelesModal.service";
import "./modals/referenceEvalModal.service";
import "./modals/interpretationOverrideModal.service";
import "./services/user.service";
import './services/ConfigService';
import './services/acmg.service';
import './services/acmgClassificationResource.service';
import './services/alleleAssessmentResource.service';
import './services/alleleFilter.service';
import './services/interpretation.service';
import './services/analysisResource.service';
import './services/interpretationResource.service';
import './services/ReferenceResource.service';
import './filters';

import './views/analysis/analysis.directive';
import './views/analysis/analysisSelection.directive';
import './views/analysis/interpretationSingleSample.directive';
import './views/assessment/variantExternalDbAssessment.directive';
import './views/assessment/variantFrequencyAssessment.directive';
import './views/assessment/variantPredictionAssessment.directive';
import './views/assessment/variantReferenceAssessment.directive';
import './views/assessment/variantReport.directive';
import './views/assessment/variantVarDbAssessment.directive';
import './views/login.directive';
import './views/navigation.directive';

import './widgets/annotationWidget.directive';
import './widgets/alleleDetailsWidget.directive';
import './widgets/analysisList.directive';
import './widgets/genomeBrowserWidget.directive';
import './widgets/frequencyDetailsWidget.directive';
import './widgets/referenceEvalWidget.directive';
import './widgets/transcriptWrapper.directive';
import './widgets/userBar.directive';
import './widgets/userBox.directive';


import {Config, Inject, Run} from './ng-decorators';


class AppConfig {

    @Config()
    @Inject('$urlRouterProvider', '$stateProvider', '$resourceProvider', '$locationProvider')
    configFactory($urlRouterProvider, $stateProvider, $resourceProvider, $locationProvider) {
        $stateProvider.state('app', {
            views: {
                app: {
                    templateUrl: 'ngtmpl/main.ngtmpl.html'
                }
            }
        })
        .state('app.analyses', {
            url: '/analyses',
            views: {
                main: {
                    template: '<analysis-selection></analysis-selection>'
                }
            }
        })
        .state('app.interpretation', {
            url: '/interpretation/:interId',
            views: {
                main: {
                    template: '<analysis interpretation-id="{{interId}}"></analysis>',
                    controller: ['$scope', '$stateParams', function($scope, $stateParams) {
                        $scope.interId = $stateParams.interId;
                    }]
                }
            }
        })
        .state('login', {
            url: '/login',
            views: {
                login: {
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
