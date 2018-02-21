export default function({ http, path, module }) {
    const excludedAlleleIds = module.get('modals.addExcludedAlleles.excludedAlleleIds')
    let count = 0
    for (let ids of Object.values(excludedAlleleIds)) {
        count += ids.length
    }
    module.set('modals.addExcludedAlleles.totalCount', count)

    module.set('modals.addExcludedAlleles.totalCount', count)
}
