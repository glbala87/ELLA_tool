import { parallel } from 'cerebral'
import loadOverviewActivities from './loadOverviewActivities'
import loadUserStats from './loadUserStats'
import progress from '../../../../common/factories/progress'

export default [
    progress('start'),
    parallel([loadOverviewActivities, loadUserStats]),
    progress('done')
]
