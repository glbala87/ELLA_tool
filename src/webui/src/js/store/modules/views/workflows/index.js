import { Module } from 'cerebral'

import { HttpProviderError } from '@cerebral/http'
import routedAnalysis from './signals/routedAnalysis'
import routedAllele from './signals/routedAllele'
import { initApp, authenticate } from '../../../common/factories'
import changeView from '../factories/changeView'
import componentChanged from './signals/componentChanged'
import selectedGenepanelChanged from './signals/selectedGenepanelChanged'
import selectedInterpretationChanged from './signals/selectedInterpretationChanged'
import copyAllAlamutClicked from './signals/copyAllAlamutClicked'
import copySelectedAlamutClicked from './signals/copySelectedAlamutClicked'
import reassignWorkflowClicked from './signals/reassignWorkflowClicked'
import startClicked from './signals/startClicked'
import finishClicked from './signals/finishClicked'
import finishConfirmationClicked from './signals/finishConfirmationClicked'
import loadInterpretationData from './signals/loadInterpretationData'
import alleleSidebar from './alleleSidebar'
import interpretation from './interpretation'
import worklog from './worklog'
import visualization from './visualization'
import verificationStatusChanged from './signals/verificationStatusChanged'

export default Module({
    state: {}, // State set in changeView (via parent module: ../workflows)
    modules: {
        alleleSidebar,
        interpretation,
        worklog,
        visualization
    },
    signals: {
        routedAllele: initApp(authenticate([changeView('workflows'), routedAllele])),
        routedAnalysis: initApp(authenticate([changeView('workflows'), routedAnalysis])),
        componentChanged,
        selectedGenepanelChanged,
        selectedInterpretationChanged,
        copySelectedAlamutClicked,
        copyAllAlamutClicked,
        reassignWorkflowClicked,
        startClicked,
        finishClicked,
        finishConfirmationClicked,
        loadInterpretationData,
        verificationStatusChanged
    }
})
