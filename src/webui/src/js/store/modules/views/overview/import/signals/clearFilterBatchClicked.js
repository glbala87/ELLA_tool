import { set } from 'cerebral/operators'
import { props } from 'cerebral/tags'
import updateCandidatesFilter from '../sequences/updateCandidatesFilter'

export default [set(props`filter`, ''), updateCandidatesFilter]
