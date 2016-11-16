import os
import json

analyses = {
    'small': [
        'brca_sample_1.HBOCUTV_v01',
        'brca_sample_1.HBOC_v01',
        'brca_sample_2.HBOCUTV_v01',
        'brca_sample_2.HBOC_v01',
        'brca_sample_3.HBOCUTV_v01',
        'brca_sample_4.HBOCUTV_v01',
        'brca_sample_5.HBOCUTV_v01',
        'brca_sample_6.HBOCUTV_v01',
        'brca_sample_7.HBOCUTV_v01',
        'brca_sample_8.HBOCUTV_v01',
        'brca_sample_master.HBOCUTV_v01'
    ],
    'all': [
        'brca_sample_1.HBOCUTV_v01',
        'brca_sample_1.HBOC_v01',
        'brca_sample_2.HBOCUTV_v01',
        'brca_sample_2.HBOC_v01',
        'brca_sample_3.HBOCUTV_v01',
        'brca_sample_4.HBOCUTV_v01',
        'brca_sample_5.HBOCUTV_v01',
        'brca_sample_6.HBOCUTV_v01',
        'brca_sample_7.HBOCUTV_v01',
        'brca_sample_8.HBOCUTV_v01',
        'brca_sample_master.HBOCUTV_v01',
        'NA12878.Bindevev_v02',
        'NA12878.Ciliopati_v03',
        'NA12878.EEogPU_v02',
        'NA12878.Iktyose_v02',
        'NA12878.Joubert_v02'
    ],
    'integration_testing': [
        'brca_sample_1.HBOCUTV_v01',
        'brca_sample_2.HBOCUTV_v01',
        'brca_sample_master.HBOCUTV_v01'
    ],
    'e2e': [
        'brca_e2e_test01.HBOCUTV_v01',
        'brca_e2e_test02.HBOCUTV_v01',
        'brca_e2e_test03.HBOCUTV_v01'
    ]
}

for tag, tag_analyses in analyses.iteritems():
    for a in tag_analyses:
        # Create dirs
        a_dir = os.path.join(tag, a)
        try:
            os.makedirs(a_dir)
        except OSError:
            pass

        # Write analysis files
        sample_name = '.'.join(a.split('.')[:-1])
        afile = {
            'name': a,
            'params': {
                'genepanel': a.split('.')[-1]
            },
            'samples': [sample_name]
        }
        with open(os.path.join(a_dir, a + '.analysis'), 'w') as f:
            json.dump(afile, f, indent=4)

        # Write sample file
        sfile = {
            'name': sample_name
        }
        with open(os.path.join(a_dir, sample_name + '.sample'), 'w') as f:
            json.dump(sfile, f, indent=4)