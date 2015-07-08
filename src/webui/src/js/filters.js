/* jshint esnext: true */

angular.module('workbench')
    .filter('split', function() {
        return function(input, splitChar, splitIndex) {
            // do some bounds checking here to ensure it has that index
            if (angular.isDefined(input)) {
                return input.split(splitChar)[splitIndex];
            }
            else {
                return input;
            }
        };
    })
    .filter('isEmpty', function() {
        return function(input) {
            return Object.keys(input).length === 0;
        };
    })
    .filter('default', () => {
        return function(input, text) {
            return input ? input : text;
        };
    });
