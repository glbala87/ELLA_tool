/* jshint esnext: true */


import {Service} from '../ng-decorators';

@Service({
    serviceName: 'Config'
})
class ConfigService {
    getConfig() {
        return {
            frequencies: {
                'ExAC': [
                    'G',
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
                ],
                'inDB': [
                    'alleleFreq',
                ]
            },
            freq_criteria: {
                'ExAC': {
                    'G': 0.01
                },
                '1000g': {
                    'G': 0.01
                },
                'inDB': {
                    'alleleFreq': 0.05
                }
            },
            variant_criteria: {
                intronic_region: {
                    '-': 20,
                    '+': 6
                }
            },
            alleleassessment: {
                days_since_update: 300
            }
        };
    }
}
