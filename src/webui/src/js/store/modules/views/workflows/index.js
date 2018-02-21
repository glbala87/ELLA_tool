import { Module } from 'cerebral'

import { HttpProviderError } from '@cerebral/http'
import routedAnalysis from './signals/routedAnalysis'
import routedAllele from './signals/routedAllele'
import { initApp, authenticate } from '../../../common/factories'
import changeView from '../factories/changeView'
import componentChanged from './signals/componentChanged'
import selectedInterpretationChanged from './signals/selectedInterpretationChanged'
import copyAllAlamutClicked from './signals/copyAllAlamutClicked'
import copySelectedAlamutClicked from './signals/copySelectedAlamutClicked'
import addExcludedAllelesOpened from './signals/addExcludedAllelesOpened'
import startClicked from './signals/startClicked'
import finishClicked from './signals/finishClicked'
import finishConfirmationClicked from './signals/finishConfirmationClicked'
import loadInterpretationData from './signals/loadInterpretationData'
import alleleSidebar from './alleleSidebar'
import interpretation from './interpretation'

export default Module({
    state: {}, // State set in changeView (via parent module: ../workflows)
    modules: {
        alleleSidebar,
        interpretation
    },
    signals: {
        routedAllele: initApp(authenticate([changeView('workflows'), routedAllele])),
        routedAnalysis: initApp(authenticate([changeView('workflows'), routedAnalysis])),
        componentChanged,
        selectedInterpretationChanged,
        copySelectedAlamutClicked,
        copyAllAlamutClicked,
        addExcludedAllelesOpened,
        startClicked,
        finishClicked,
        finishConfirmationClicked,
        loadInterpretationData
    }
})
