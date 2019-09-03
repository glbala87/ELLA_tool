/* jshint esnext: true */

import { Filter, Inject } from './ng-decorators'

class Filters {
    /*
    Convert one or several gene panel values to a string value
    */

    @Filter({
        filterName: 'omimLink'
    })
    // Retrun url of symbol search if the gene entry ID is missing
    omimLinkFilter() {
        return (entryID, symbol) => {
            const base = 'https://www.omim.org/'
            return entryID ? base + `entry/${entryID}` : base + `/search/?search=${symbol}`
        }
    }

    @Filter({
        filterName: 'hgmdLink'
    })
    hgmdLinkFilter() {
        return (gene) => {
            return gene
                ? `https://portal.biobase-international.com/hgmd/pro/gene.php?gene=${gene}`
                : ''
        }
    }

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
}

export default Filter
