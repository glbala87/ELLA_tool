/* jshint esnext: true */

import { Filter, Inject } from './ng-decorators'

class Filters {
    @Filter({
        filterName: 'noUnderscores'
    })
    noUnderscores() {
        return (text) => {
            if (!text) {
                return ''
            }
            return text.replace(/_/g, ' ')
        }
    }

    @Filter({
        filterName: 'dropREQ'
    })
    dropREQ() {
        return (text) => {
            return text.replace(/REQ_GP/g, 'GP - ').replace(/REQ_/g, 'R - ')
        }
    }

    @Filter({
        filterName: 'killLeadingDashes'
    })
    killLeadingDashes() {
        return (text) => {
            return text.replace(/^-\s/g, '')
        }
    }

    @Filter({
        filterName: 'formatText'
    })
    formatText() {
        return (input) => {
            if (!input) return input
            var output = input
                //replace possible line breaks.
                .replace(/(\\r\\n|\\r|\\n)/g, '<br/>')
                //replace tabs
                .replace(/\\t/g, '&nbsp;&nbsp;&nbsp;')
                //replace spaces.
                .replace(/ /g, '&nbsp;')
                .replace(/"|'/g, '')
            return output
        }
    }

    @Filter({
        filterName: 'trusted'
    })
    @Inject('$sce')
    trustedHTML($sce) {
        return (html) => {
            return $sce.trustAsHtml(html)
        }
    }

    @Filter({
        filterName: 'formatNumber'
    })
    formatNumber() {
        // Revert to scientific notation for float
        // Call with arguments like {{ input | formatNumber:precision:scientific_threshold}}
        return (input, precision, scientificThreshold) => {
            precision = precision === undefined ? 6 : precision
            scientificThreshold = scientificThreshold === undefined ? 4 : scientificThreshold
            if (isNaN(input)) {
                return input
            } else if (Number.isInteger(input)) {
                return input
            } else if (input < Math.pow(10, -scientificThreshold)) {
                return input.toExponential(precision - scientificThreshold + 1)
            } else {
                return input.toFixed(precision)
            }
        }
    }
}

export default Filter
