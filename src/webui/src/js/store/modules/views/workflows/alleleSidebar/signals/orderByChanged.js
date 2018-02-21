import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toggleOrderBy from '../actions/toggleOrderBy'
import sortSections from '../actions/sortSections'

export default [toggleOrderBy, sortSections]
