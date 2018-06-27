export default function checkQuery({ module, path }) {
    const query = module.get('query')
    const a = query.type
    const b = query.freetext
    const c = query.gene
    const d = query.user

    if (d) {
        // Always allow search on user
        return path.true()
    } else if (b && b.length > 2 && (c || a === 'analyses')) {
        // Allow search if freetext length > 2 if gene is specified (alleles) or if type is analyses
        return path.true()
    } else if (b && b.match(/.*:.*/g)) {
        // Allow search if searching for full HGVSc
        return path.true()
    } else {
        return path.false()
    }
}
