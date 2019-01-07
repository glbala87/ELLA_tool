import { Compute } from 'cerebral';
import getAlleleState from './getAlleleState';

export default function(alleleId) {
    return Compute(getAlleleState(alleleId), (alleleState) => {
        if (alleleState) {
            return Boolean(alleleState.alleleassessment.reuse)
        }
        return false
    })
}
