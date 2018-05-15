export default function checkQuery({ module, path }) {
    const query = module.get('query')
    const a = query.freetext
    const b = query.gene
    const c = query.user

    if (a && (!b && !c)) {
        if (a.length > 2) {
            return path.true()
        }
        return path.false()
    } else {
        if (b || c) {
            return path.true()
        }
        return path.false()
    }
}
