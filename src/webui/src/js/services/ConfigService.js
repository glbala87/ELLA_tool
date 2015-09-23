/* jshint esnext: true */
/* jshint esnext: true */

angular.module('workbench')
    .factory('Config', [function () {

        return {
            getConfig: function () {

                return {
                    'frequencies': {
                        'ExAC': [
                            'AFR',
                            'AMR',
                            'EAS',
                            'FIN',
                            'NFE',
                            'OTH',
                            'SAS',
                        ],
                        '1000g': [
                            'G',
                            'AMR',
                            'ASN',
                            'EUR',
                            'AA',
                            'EA',
                            'EAS',
                            'SAS'
                        ]
                    },
                    freq_criteria: {
                        'ExAC': 0.01,
                        '1000g': 0.01
                    },
                    alleleassessment: {
                        days_since_update: 300
                    }
                };

            }
        };

    }]);
