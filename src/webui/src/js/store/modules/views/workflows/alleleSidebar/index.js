import { Module } from 'cerebral'
import selectedAlleleChanged from './signals/selectedAlleleChanged'
import includeReportToggled from './signals/includeReportToggled'
import orderByChanged from './signals/orderByChanged'
import toggleExpanded from './signals/toggleExpanded'
import quickClassificationClicked from './signals/quickClassificationClicked'

export default Module({
    state: {},
    signals: {
        selectedAlleleChanged,
        includeReportToggled,
        orderByChanged,
        toggleExpanded,
        quickClassificationClicked
    }
})
