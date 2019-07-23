import { sequence, parallel } from 'cerebral'
import loadActiveImports from './loadActiveImports'
import loadImportHistory from './loadImportHistory'

export default sequence('loadImportJobs', [parallel([loadActiveImports, loadImportHistory])])
