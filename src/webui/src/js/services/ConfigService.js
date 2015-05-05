/* jshint esnext: true */
/* jshint esnext: true */

angular.module('workbench')
    .factory('Config', [function() {

    return {
        getConfig: function() {

            return {
                'frequencies': {
                    exac: [
                        // field, display name
                        ['AFR', 'AFR'],
                        ['AMR', 'AMR'],
                        ['EAS', 'EAS'],
                        ['FIN', 'FIN'],
                        ['NFE', 'NFE'],
                        ['OTH', 'OTH'],
                        ['SAS', 'SAS'],
                    ],
                    thousand_g: [
                        ['GMAF', 'G'],
                        ['AMR_MAF', 'AMR'],
                        ['ASN_MAF', 'ASN'],
                        ['ASN_MAF', 'ASN'],
                        ['EUR_MAF', 'EUR']
                    ],
                    esp6500: [
                        ['AA_MAF', 'AA'],
                        ['EA_MAF', 'EA']
                    ]
                }
            };

        }
    };

}]);
