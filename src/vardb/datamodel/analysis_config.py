

class AnalysisConfigData(object):
    def __init__(self, vcf_path, analysis_name, gp_name, gp_version, priority):
        self.vcf_path = vcf_path
        self.analysis_name = analysis_name 
        self.gp_name = gp_name
        self.gp_version = gp_version
        self.priority = priority
