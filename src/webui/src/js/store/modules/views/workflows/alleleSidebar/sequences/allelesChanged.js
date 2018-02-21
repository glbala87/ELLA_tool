import { Compute } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../actions/prepareSelectedAllele'
import sortSections from '../actions/sortSections'

export default [sortSections, prepareSelectedAllele]
