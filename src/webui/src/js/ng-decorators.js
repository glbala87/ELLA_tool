/* jshint esnext: true */

import angular from 'angular'
import uiBootstrap from 'angular-ui-bootstrap'
import 'angular-animate'
import 'angular-resource'
import 'angular-sanitize'
import angularChecklistModel from 'checklist-model'
import angularSelector from 'angular-selector'
import { addModule, connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

addModule(angular)

export let app = angular.module('workbench', [
    uiBootstrap,
    'ngResource',
    'ngAnimate',
    'ngSanitize',
    angularChecklistModel,
    'selector',
    'templates',
    'cerebral'
])

// For using letting ngModel watch an external attribute and copy
// value upon changes. Let's us bind to Cerebral store, while using
// internal model in controller for keeping view value.
// Needed since AngularJS doesn't support one-way models.
const ngModelWatchDirective = [
    '$rootScope',
    function($rootScope) {
        return {
            restrict: 'A',
            require: ['ngModel'],
            controller: [
                '$scope',
                '$parse',
                '$attrs',
                function($scope, $parse, $attrs) {
                    // Store $parse on scope, as we need this when child scopes have been created in link-function
                    $scope.$$parseFunc = $parse
                    const key = $attrs.ngModel + $attrs.ngModelWatch

                    // Create cache for parse-functions. This should not be populated here, as we need child scopes to be created
                    // (e.g. for ngRepeat), available in link-function
                    if (!('$$parsedNgModelWatch' in $scope)) {
                        $scope.$$parsedNgModelWatch = {}
                    }

                    // We cache the ngModel value, to evaluate whether to set a new ngModel value
                    if (!('$$ngModelWatchPrevious' in $scope)) {
                        $scope.$$ngModelWatchPrevious = {}
                    }
                    // Initialize with ngModel value, to avoid an unnecessary ngModelSet below
                    if (!(key in $scope.$$ngModelWatchPrevious)) {
                        $scope.$$ngModelWatchPrevious[key] = $scope.$$parseFunc($attrs.ngModel)(
                            $scope
                        )
                    }
                }
            ],
            link: function(scope, element, attr, ctrls) {
                const ngModel = ctrls[0]

                // Use combination of ngModel and ngModelWatch as key, as this should be unique in behaviour
                const key = attr.ngModel + attr.ngModelWatch

                // Cache parsed ngModelWatch to avoid calling $parse many times
                //
                // Do not move to controller, as we need to wait for other directives (e.g. ngRepeat)
                // to create child scopes
                if (!(key in scope.$$parsedNgModelWatch)) {
                    scope.$$parsedNgModelWatch[key] = scope.$$parseFunc(attr.ngModelWatch)
                }

                scope.$watch(
                    () => {
                        // Evaluate whether ngModelWatch has changed
                        return JSON.stringify({
                            ngModelWatchValue: scope.$$parsedNgModelWatch[key](scope),
                            ngModelValue: attr.ngModelWatch
                        })
                    },

                    (n, o) => {
                        let current = JSON.parse(n).ngModelWatchValue
                        let previous = scope.$$ngModelWatchPrevious[key]

                        // If the ngModelWatch value is different from the previous ngModelWatch value, we update ngModel
                        if (current !== previous) {
                            ngModel.$$ngModelSet(scope, current)
                            scope.$$ngModelWatchPrevious[key] = current
                        }
                    }
                )
            }
        }
    }
]

app.directive('ngModelWatch', ngModelWatchDirective)

function Run() {
    return function decorator(target, key, descriptor) {
        app.run(descriptor.value)
    }
}

function Config() {
    return function decorator(target, key, descriptor) {
        app.config(descriptor.value)
    }
}

function Service(options) {
    return function decorator(target) {
        options = options ? options : {}
        if (!options.serviceName) {
            throw new Error('@Service() must contains serviceName property!')
        }
        app.service(options.serviceName, target)
    }
}

function Filter(filter) {
    return function decorator(target, key, descriptor) {
        filter = filter ? filter : {}
        if (!filter.filterName) {
            throw new Error('@Filter() must contains filterName property!')
        }
        app.filter(filter.filterName, descriptor.value)
    }
}

function Inject(...dependencies) {
    return function decorator(target, key, descriptor) {
        // if it's true then we injecting dependencies into function and not Class constructor
        if (descriptor) {
            const fn = descriptor.value
            fn.$inject = dependencies
        } else {
            target.$inject = dependencies
        }
    }
}

function DashToCamelCase(input) {
    return input.replace(/-([a-z])/g, function(g) {
        return g[1].toUpperCase()
    })
}

function Directive(options) {
    let defaults = {
        restrict: 'E',
        scope: {},
        bindToController: true,
        controllerAs: 'vm'
    }
    return function decorator(target) {
        let new_options = {}
        Object.assign(new_options, defaults)
        Object.assign(new_options, options)

        let controllerClassName = options.controllerClassName || target.name
        new_options.controller = target
        app.controller(controllerClassName, target)

        // In order for two-way binding to work properly with bindToController,
        // both bindToController and scope must be the same object.
        // Otherwise watches watching on a property on the scope will not fire when
        // the property is updated.
        if (new_options.bindToController === true) {
            new_options.bindToController = new_options.scope
        }
        app.directive(DashToCamelCase(new_options.selector), () => new_options)
    }
}

export default app
export { Inject, Run, Config, Service, Filter, Directive }
