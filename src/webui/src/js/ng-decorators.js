/* jshint esnext: true */


let app = angular.module('workbench', ['ui.bootstrap',
    'ui.router',
    'ngResource',
    'ngAnimate',
    'ngRoute',
    'ngCookies',
    'checklist-model'
]);


function Run() {
    return function decorator(target, key, descriptor) {
        app.run(descriptor.value);
    };
}

function Config() {
    return function decorator(target, key, descriptor) {
        app.config(descriptor.value);
    };
}

function Service(options) {
    return function decorator(target) {
        options = options ? options : {};
        if (!options.serviceName) {
            throw new Error('@Service() must contains serviceName property!');
        }
        app.service(options.serviceName, target);
    };
}

function Filter(filter) {
    return function decorator(target, key, descriptor) {
        filter = filter ? filter : {};
        if (!filter.filterName) {
            throw new Error('@Filter() must contains filterName property!');
        }
        app.filter(filter.filterName, descriptor.value);
    };
}

function Inject(...dependencies) {
    return function decorator(target, key, descriptor) {
        // if it's true then we injecting dependencies into function and not Class constructor
        if(descriptor) {
            const fn = descriptor.value;
            fn.$inject = dependencies;
        } else {
            target.$inject = dependencies;
        }
    };
}

function DashToCamelCase(input) {
    return input.replace(/-([a-z])/g, function (g) { return g[1].toUpperCase(); });
}


function Directive(options) {
    let defaults = {
        restrict: 'E',
        scope: {},
        bindToController: true,
        controllerAs: 'vm'
    };
    return function decorator(target) {
        let new_options = {};
        Object.assign(new_options, defaults);
        Object.assign(new_options, options);
        new_options.controller = target;
        // In order for two-way binding to work properly with bindToController,
        // both bindToController and scope must be the same object.
        // Otherwise watches watching on a property on the scope will not fire when
        // the property is updated.
        if (new_options.bindToController === true) {
            new_options.bindToController = new_options.scope;
        }
        app.directive(DashToCamelCase(new_options.selector), () => new_options);
    };
}


export default app;
export {Inject, Run, Config, Service, Filter, Directive};
