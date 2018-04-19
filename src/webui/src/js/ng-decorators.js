/* jshint esnext: true */

import { addModule, connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

addModule(angular)

export let app = angular.module('workbench', [
    'ui.bootstrap',
    'templates',
    'ngResource',
    'ngAnimate',
    'ngRoute',
    'ngCookies',
    'checklist-model',
    'angular-clipboard',
    'toastr',
    'selector',
    'ngSanitize',
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
                    // HACK: Scope is shared between all ngModel.
                    // Store the get() function created with it's attr string
                    if (!$scope.$$parsedNgModelWatch) {
                        $scope.$$parsedNgModelWatch = {}
                    }
                    $scope.$$parsedNgModelWatch[$attrs.ngModelWatch] = $parse($attrs.ngModelWatch)
                }
            ],
            link: function(scope, element, attr, ctrls) {
                const ngModel = ctrls[0]

                scope.$watch(
                    () => {
                        // HACK: Use attr ngModelWatch attr string to get the get() function
                        return scope.$$parsedNgModelWatch[attr.ngModelWatch](scope)
                    },
                    (n, o) => {
                        ngModel.$$ngModelSet(scope, n)
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
