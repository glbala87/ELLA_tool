import { set } from 'cerebral/operators';
import { props } from 'cerebral/tags';
import showModal from '../../../../common/actions/showModal';

export default [set(props`modalName`, 'finishConfirmation'), showModal]
