

class AnalysisConfigData(object):
    def __init__(self, vcf_path, analysis_name, gp_name, gp_version, priority=1, date_requested=None, ped_path=None, report=None, warnings=None):
        self.vcf_path = vcf_path
        self.ped_path = ped_path
        self.analysis_name = analysis_name
        self.gp_name = gp_name
        self.gp_version = gp_version
        self.priority = priority
        self.date_requested = date_requested
        self.report = report
        self.warnings = warnings
