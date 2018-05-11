import { Module } from 'cerebral'
import addExcludedAllelesClicked from './signals/addExcludedAllelesClicked'
import categoryChanged from './signals/categoryChanged'
import geneChanged from './signals/geneChanged'
import pageChanged from './signals/pageChanged'
import includeAlleleClicked from './signals/includeAlleleClicked'
import excludeAlleleClicked from './signals/excludeAlleleClicked'
import closeAddExcludedClicked from './signals/closeAddExcludedClicked'

export default Module({
    state: {},
    signals: {
        addExcludedAllelesClicked,
        categoryChanged,
        geneChanged,
        pageChanged,
        includeAlleleClicked,
        excludeAlleleClicked,
        closeAddExcludedClicked
    }
})
