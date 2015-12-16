/* jshint esnext: true */

import {Filter} from './ng-decorators';

class Filters {

    @Filter({
        filterName: 'split'
    })
    splitFilter() {
        return (input, splitChar, splitIndex) => {
            // do some bounds checking here to ensure it has that index
            if (input !== undefined) {
                return input.split(splitChar)[splitIndex];
            } else {
                return input;
            }
        };
    }

    @Filter({
        filterName: 'isEmpty'
    })
    isEmptyFilter() {
        return (input) => {
            return Object.keys(input).length === 0;
        };
    }

    @Filter({
        filterName: 'default'
    })
    defaultFilter() {
        return (input, text) => {
            return input ? input : text;
        };
    }

    @Filter({
        filterName: 'HGVSc_short'
    })
    HGVSc_shortFilter() {
        return (input) => {
            if (input) {
                return input.split(':')[1];
            }
            return '';
        };
    }

    @Filter({
        filterName: 'HGVSp_short'
    })
    HGVSp_shortFilter() {
        return (input) => {
            if (input) {
                return input.split(':')[1];
            }
            return '';
        };
    }

    @Filter({
        filterName: 'secondsToTimeString'
    })
    secondsToTimeStringFilter() {
        return (seconds) => {
            if (!seconds) {
                return '';
            }
            var days = Math.floor(seconds / 86400);
            var hours = Math.floor((seconds % 86400) / 3600);
            var minutes = Math.floor(((seconds % 86400) % 3600) / 60);
            var timeString = '';
            if(days > 0) timeString += (days > 1) ? (days + " days ") : (days + " day ");
            if(hours > 0) timeString += (hours > 1) ? (hours + "h ") : (hours + "h ");
            if(minutes >= 0) timeString += (minutes > 1) ? (minutes + " min ") : (minutes + " min ");
            return timeString;
        };
    }

    @Filter({
        filterName: 'prettyJSON'
    })
    prettyJSONFilter() {
        return (json) => {
          return JSON ? JSON.stringify(json, null, '  ') : 'your browser doesnt support JSON so cant pretty print';
        }
    }

}

export default Filter;
