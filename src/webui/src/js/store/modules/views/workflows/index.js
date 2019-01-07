import { Module } from 'cerebral';
import { authenticate, initApp } from '../../../common/factories';
import changeView from '../factories/changeView';
import alleleSidebar from './alleleSidebar';
import interpretation from './interpretation';
import componentChanged from './signals/componentChanged';
import copyAllAlamutClicked from './signals/copyAllAlamutClicked';
import copySelectedAlamutClicked from './signals/copySelectedAlamutClicked';
import finishClicked from './signals/finishClicked';
import finishConfirmationClicked from './signals/finishConfirmationClicked';
import loadInterpretationData from './signals/loadInterpretationData';
import notRelevantChanged from './signals/notRelevantChanged';
import reassignWorkflowClicked from './signals/reassignWorkflowClicked';
import routedAllele from './signals/routedAllele';
import routedAnalysis from './signals/routedAnalysis';
import selectedGenepanelChanged from './signals/selectedGenepanelChanged';
import selectedInterpretationChanged from './signals/selectedInterpretationChanged';
import startClicked from './signals/startClicked';
import verificationStatusChanged from './signals/verificationStatusChanged';
import visualization from './visualization';
import worklog from './worklog';


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
        verificationStatusChanged,
        notRelevantChanged
    }
})
