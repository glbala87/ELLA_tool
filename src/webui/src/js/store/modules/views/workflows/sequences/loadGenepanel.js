import { sequence } from 'cerebral';
import { set } from 'cerebral/operators';
import { props, state } from 'cerebral/tags';
import toast from '../../../../common/factories/toast';
import getGenepanel from '../actions/getGenepanel';


export default sequence('loadGenepanel', [
    getGenepanel,
    {
        error: [toast('error', 'Failed to load genepanel', 30000)],
        success: [set(state`views.workflows.data.genepanel`, props`result`)]
    }
])
