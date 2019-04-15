import { Module } from 'cerebral'
import showAddExcludedAllelesClicked from './signals/showAddExcludedAllelesClicked'
import categoryChanged from './signals/categoryChanged'
import geneChanged from './signals/geneChanged'
import pageChanged from './signals/pageChanged'
import includeAlleleClicked from './signals/includeAlleleClicked'
import excludeAlleleClicked from './signals/excludeAlleleClicked'
import closeAddExcludedClicked from './signals/closeAddExcludedClicked'

export default Module({
    state: {
        show: false
    },
    signals: {
        showAddExcludedAllelesClicked,
        categoryChanged,
        geneChanged,
        pageChanged,
        includeAlleleClicked,
        excludeAlleleClicked,
        closeAddExcludedClicked
    }
})
