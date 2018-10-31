module.exports = {
	title: 'ella documentation',
	
	head: [
		['link', { rel: 'shortcut icon', type: "image/x-icon", href: `./favicon.png` }]
	],
	
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
                    title: 'Basics',
                    collapsable: false,
                    children: [
						'/manual/',
						'/manual/save-and-finish'
					]
                },
				{
                    title: 'OVERVIEW page',
                    collapsable: false,
                    children: [
						'/manual/overview-page' 
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
                        '/manual/side-bar',
                        '/manual/evidence-sections',
                        '/manual/classification-section'
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
            '/technical/': [
                {
                    title: 'Technical documentation',
                    collapsable: false,
                    children: [
                        '/technical/',
                        '/technical/deployment',
                        '/technical/development',
                        '/technical/workflow',
                        '/technical/datamodel',
                        '/technical/uicomponents',
                        '/technical/testing',
                        '/technical/acmg-rule-engine',
                        '/technical/preconfigured-gene-panels',
                        '/technical/readme-gitlab'
                    ]
                }
            ]
        }
		
		/* Alternative sidebar
		sidebar: [
			'/',
			{ title: 'User manual',
				children: [
					'/manual/',
					'/manual/overview-page',
					'/manual/info-page',
					'/manual/classification-page',
					'/manual/top-bar',
					'/manual/side-bar',
					'/manual/evidence-sections',
					'/manual/classification-section',
					'/manual/report-page',
					'/manual/save-and-finish'
				]
			},
			{ title: 'Technical documentation',
				children: [
					'/technical/',
					'/technical/installation',
					'/technical/workflow',
					'/technical/datamodel',
					'/technical/uicomponents',
					'/technical/testing',
					'/technical/acmg-rule-engine',
					'/technical/preconfigured-gene-panels',
					'/technical/readme-gitlab'
				]
			},
			'/releasenotes/'
		]
		*/
		
	}
}