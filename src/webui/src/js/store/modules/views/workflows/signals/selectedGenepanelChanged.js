import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadAlleles from '../sequences/loadAlleles'
import loadGenepanel from '../sequences/loadGenepanel'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import progress from '../../../../common/factories/progress'
import loadAcmg from '../sequences/loadAcmg'

export default [
    progress('start'),
    set(state`views.workflows.selectedGenepanel`, props`genepanel`),
    loadGenepanel,
    loadAlleles,
    progress('inc'),
    loadAcmg,
    progress('inc'),
    // This signal is only relevant in allele workflow
    setNavbarTitle(
        string`${state`views.workflows.data.alleles.${state`views.workflows.id`}.formatted.display`} (${state`views.workflows.selectedGenepanel.name`}_${state`views.workflows.selectedGenepanel.version`})`
    ),
    progress('done')
]
