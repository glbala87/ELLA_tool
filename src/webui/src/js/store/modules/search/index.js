import { Module } from 'cerebral'

import queryChanged from './signals/queryChanged'
import pageChanged from './signals/pageChanged'
import optionsSearchChanged from './signals/optionsSearchChanged'
import modals from './modals'

export default Module({
    state: {
        query: {
            freetext: null,
            gene: null,
            user: null
        },
        page: 1,
        per_page: 10,
        limit: 100,
        options: {
            genepanel: null,
            user: null
        },
        results: null,
        loading: false
    },
    signals: {
        optionsSearchChanged,
        queryChanged,
        pageChanged
    },
    modules: {
        modals
    }
})
