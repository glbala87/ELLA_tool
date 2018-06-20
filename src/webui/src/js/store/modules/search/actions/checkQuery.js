export default function checkQuery({ module, path }) {
    const query = module.get('query')
    const a = query.type
    const b = query.freetext
    const c = query.gene
    const d = query.user
    if (a === 'alleles')
        if (b && (c || d)) {
            if (b.length > 2) {
                return path.true()
            }
            return path.false()
        } else if (b && b.match(/.*:.*/g)) {
            return path.true()
        } else if (c || d) {
            return path.true()
        } else {
            return path.false()
        }
    else if ((b && b.length > 2) || d) {
        return path.true()
    } else {
        return path.false()
    }
}
