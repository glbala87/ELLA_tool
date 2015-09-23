/* jshint esnext: true */

angular.module('workbench')
    .filter('split', function () {
        return function (input, splitChar, splitIndex) {
            // do some bounds checking here to ensure it has that index
            if (angular.isDefined(input)) {
                return input.split(splitChar)[splitIndex];
            } else {
                return input;
            }
        };
    })
    .filter('isEmpty', function () {
        return function (input) {
            return Object.keys(input).length === 0;
        };
    })
    .filter('default', () => {
        return function (input, text) {
            return input ? input : text;
        };
    })
    .filter('HGVSc_short', () => {
        return function (input) {
            if (input) {
                return input.split(':')[1];
            }
            return '';
        };
    })
    .filter('HGVSp_short', () => {
        return function (input) {
            if (input) {
                return input.split(':')[1];
            }
            return '';
        };
    })
    .filter('secondsToTimeString', () => {
        return function (seconds) {
            if (!seconds) {
                return '';
            }
            var days = Math.floor(seconds / 86400);
            var hours = Math.floor((seconds % 86400) / 3600);
            var minutes = Math.floor(((seconds % 86400) % 3600) / 60);
            var timeString = '';
            if (days > 0) timeString += (days > 1) ? (days + " days ") : (days + " day ");
            if (hours > 0) timeString += (hours > 1) ? (hours + " h ") : (hours + " h ");
            if (minutes >= 0) timeString += (minutes > 1) ? (minutes + " min ") : (minutes + " min ");
            return timeString;
        };
    });
