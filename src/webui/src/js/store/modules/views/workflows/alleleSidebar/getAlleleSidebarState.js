export default function getAlleleSidebarState() {
    return {
        callerTypes: ['snv', 'cnv'],
        callerTypeSelected: 'snv',
        classificationType: 'full',
        classificationTypes: ['full', 'quick', 'visual'],
        unclassified: null,
        classified: null,
        technical: null,
        orderBy: {
            unclassified: {
                key: null,
                reverse: false
            },
            classified: {
                key: null,
                reverse: false
            },
            technical: {
                key: null,
                reverse: false
            },
            notRelevant: {
                key: null,
                reverse: false
            }
        }
    }
}
