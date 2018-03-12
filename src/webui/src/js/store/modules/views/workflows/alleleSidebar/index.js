import { Module } from 'cerebral'
import selectedAlleleChanged from './signals/selectedAlleleChanged'
import includeReportToggled from './signals/includeReportToggled'
import orderByChanged from './signals/orderByChanged'

export default Module({
    state: {},
    signals: {
        selectedAlleleChanged,
        includeReportToggled,
        orderByChanged
    }
})
