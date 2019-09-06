import { parallel } from 'cerebral'
import loadUserStats from './loadUserStats'
import loadUsers from './loadUsers'
import progress from '../../../../common/factories/progress'

export default [progress('start'), parallel([loadUsers, loadUserStats]), progress('done')]
