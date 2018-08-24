import { default as isReadOnlyCompute } from '../../computed/isReadOnly'

export default function isReadOnly({ path, resolve }) {
    if (resolve.value(isReadOnlyCompute)) {
        return path.true()
    }
    return path.false()
}
