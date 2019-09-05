import { Module } from 'cerebral'
import closeClicked from './signals/closeClicked'
import showGenepanelOverviewClicked from './signals/showGenepanelOverviewClicked'
import copyGenesToClipboardClicked from './signals/copyGenesToClipboardClicked'
import geneFilterChanged from './signals/geneFilterChanged'
import filteredGenesPageChanged from './signals/filteredGenesPageChanged'

export default Module({
    state: {
        show: false
    },
    signals: {
        closeClicked,
        showGenepanelOverviewClicked,
        copyGenesToClipboardClicked,
        geneFilterChanged,
        filteredGenesPageChanged
    }
})
