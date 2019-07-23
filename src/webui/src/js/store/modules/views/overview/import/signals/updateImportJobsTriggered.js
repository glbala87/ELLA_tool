import loadImportJobs from '../sequences/loadImportJobs'
import progress from '../../../../../common/factories/progress'

export default [progress('start'), loadImportJobs, progress('done')]
