module.exports = {
    title: 'ELLA documentation',
    base: '/docs/',

    head: [['link', { rel: 'shortcut icon', type: 'image/x-icon', href: `./favicon.png` }]],

    themeConfig: {
        lastUpdated: 'Last Updated', // string | boolean

        nav: [
            { text: 'Home', link: '/' },
            { text: 'User interface', link: '/manual/' },
            { text: 'Concepts', link: '/concepts/' },
            { text: 'Technical documentation', link: '/technical/' },
            { text: 'Release notes', link: '/releasenotes/' },
            { text: 'allel.es', link: 'http://allel.es' }
        ],

        sidebarDepth: 2,

        sidebar: {
            '/manual/': [
                {
                    title: 'User interface',
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
                        '/manual/visual'
                    ]
                },
                {
                    title: 'REPORT page',
                    collapsable: false,
                    children: [
                        '/manual/report-page'
                    ]
                }
            ],
            '/concepts/': [
                {
                    title: 'Concepts',
                    collapsable: false,
                    children: [
                        '/concepts/',
                        '/concepts/workflows',
                        '/concepts/filtering',
                        '/concepts/acmg-rule-engine',
                        '/concepts/gene-panels'
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
                        '/technical/genepanels',
                        '/technical/filtering',
                        '/technical/acmg',
                        '/technical/import',
                        '/technical/uioptions' 
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
