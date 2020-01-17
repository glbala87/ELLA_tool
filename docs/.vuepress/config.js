module.exports = {
    title: 'ELLA documentation',
    base: '/docs/',

    head: [['link', { rel: 'shortcut icon', type: 'image/x-icon', href: `./favicon.png` }]],

    themeConfig: {
        lastUpdated: 'Last Updated', // string | boolean

        nav: [
            { text: 'Home', link: '/' },
            { text: 'User manual', link: '/manual/' },
            { text: 'Technical documentation', link: '/technical/' },
            { text: 'Release notes', link: '/releasenotes/' },
            { text: 'allel.es', link: 'http://allel.es' }
        ],

        sidebarDepth: 2,

        sidebar: {
            '/manual/': [
                {
                    title: 'User manual',
                    collapsable: false,
                    children: [
                        '/manual/'
                    ]
                },
                {
                    title: 'OVERVIEW page',
                    collapsable: false,
                    children: [
                        '/manual/choosing-sample-variant',
                        '/manual/data-import-reanalyses',
                        '/manual/export-sanger'
                    ]
                },
                {
                    title: 'INFO page',
                    collapsable: false,
                    children: [
                        '/manual/info-page'
                    ]
                },
                {
                    title: 'CLASSIFICATION page',
                    collapsable: false,
                    children: [
                        '/manual/classification-page',
                        '/manual/top-bar',
                        '/manual/worklog',
                        '/manual/side-bar',
                        '/manual/filtered-variants',
                        '/manual/evidence-sections',
                        '/manual/classification-section',
                        '/manual/quick-classification',
                        '/manual/visual',
                        '/manual/warnings'
                    ]
                },
                {
                    title: 'REPORT page',
                    collapsable: false,
                    children: [
                        '/manual/report-page'
                    ]
                },
                {
                    title: 'Concepts',
                    collapsable: false,
                    children: [
                        '/manual/concepts',
                        '/manual/workflows',
                        '/manual/acmg-rule-engine',
                        '/manual/gene-panels'                        
                    ]
                }
            ],
            '/technical/': [
                {
                    title: 'Technical documentation',
                    collapsable: false,
                    children: [
                        '/technical/'
                    ]
                },
                {
                    title: 'Setup',
                    collapsable: false,
                    children: [
                        '/technical/setup',
                        '/technical/demo',
                        '/technical/production',
                        '/technical/logging',
                        '/technical/development',
                        '/technical/testing'
                    ]
                },
                {
                    title: 'Configuration',
                    collapsable: false,
                    children: [
                        '/technical/configuration',
                        '/technical/users',
                        '/technical/uioptions',
                        '/technical/annotation',
                        '/technical/genepanels',
                        '/technical/import',
                        '/technical/filtering',
                        '/technical/acmg'
                    ]
                },
                {
                    title: 'System internals',
                    collapsable: false,
                    children: [
                        '/technical/sysinternals',
                        '/technical/workflow',
                        '/technical/datamodel',
                        '/technical/uicomponents'
                    ]
                }
            ],
            '/releasenotes/': [
                {
                    title: 'Release notes',
                    collapsable: false,
                    children: [
                        '/releasenotes/',
                        '/releasenotes/olderreleases'
                    ]
                }
            ]
        }
    }
}
