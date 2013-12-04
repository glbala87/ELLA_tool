import wx
import controller.details

#----------------------------------------------------------------------
class ButtonBar(wx.Panel):
    def __init__(self, parent, *argc):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        main_frame = self.GetTopLevelParent()
        buttons = []
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label in argc:
            button =wx.Button(self, wx.ID_ANY, label, name=label)
            button.Bind(wx.EVT_BUTTON, main_frame.on_button)
            buttons.append(button)
            sizer.Add(button, 1, wx.ALL, 20)
        self.SetSizer(sizer)
    def on_button():
        pass
                                   
#----------------------------------------------------------------------
class DetailsHeaders(list):
    def __init__(self, parent):
        list.__init__(self)
        self.append(wx.StaticText(parent, wx.ID_ANY, "Gene"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "HGVS cDNA"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "Observed genotype"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "Reason for VarDB class"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "Effect"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "BIC"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "HGMD Pro"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "SIFT"))
        self.append(wx.StaticText(parent, wx.ID_ANY, "MutationTaster"))
        
#----------------------------------------------------------------------    
class DetailsCtrls(list):
    def __init__(self, parent, details):
        list.__init__(self)
        #Append xwCtrl and proportion:
        self.append(wx.StaticText(parent, wx.ID_ANY, details["gene"],
                                name="gene"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["hgvs_cdna"],
                                name="hgvs_cdna"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["observed_genotype"],
                                name="observed_genotype"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["reason_for_vardb_class"],
                                style=wx.TE_MULTILINE, name="reason_for_vardb_class"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["effect"],
                                style=wx.TE_MULTILINE, name="effect"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["bic"],
                                style=wx.TE_MULTILINE, name="bic"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["hgmd_pro"],
                                style=wx.TE_MULTILINE, name="hgmd_pro"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["sift"],
                                style=wx.TE_MULTILINE, name="sift"))
        self.append(wx.StaticText(parent, wx.ID_ANY, details["mutation_taster"],
                                style=wx.TE_MULTILINE, name="mutation_taster"))

#----------------------------------------------------------------------
class DetailsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour('#efefef')
        self.details = controller.details.get_details_record("", "")[0]
        self.gene = self.details['gene']
        self.variant = self.details['hgvs_cdna']
        self.h1 = wx.StaticText(self, wx.ID_ANY,
                    "Details for variant %s %s" % (self.gene, self.variant))
        self.h1.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        p = wx.Panel(self, style=wx.SUNKEN_BORDER)
        p.SetBackgroundColour(wx.WHITE)
        self.headers = DetailsHeaders(p)
        self.ctrls = DetailsCtrls(p, self.details)
        self.button_bar = ButtonBar(self, "<<<  Previous", "Next  >>>")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.h1, 0, wx.ALL, 10)
        b_sizer = wx.BoxSizer(wx.VERTICAL)
        for i in range(len(self.headers)):
            s = wx.BoxSizer(wx.HORIZONTAL)
            s.Add(self.headers[i], 1, wx.EXPAND|wx.ALL, 1)
            s.Add(self.ctrls[i], 2, wx.EXPAND|wx.ALL, 1)
            b_sizer.Add(s, 1, wx.EXPAND|wx.ALL, 1)
            b_sizer.Add(wx.StaticLine(p, wx.ID_ANY,
                                style=wx.LI_HORIZONTAL), 0, wx.ALL|wx.EXPAND, 0)
        p.SetSizer(b_sizer)
        sizer.Add(p,  1, wx.EXPAND|wx.ALL, 1)
        sizer.AddStretchSpacer()
        sizer.Add(self.button_bar, 0, wx.EXPAND|wx.ALIGN_RIGHT)
        self.SetSizer(sizer)

    def new_obj(self, obj):
        gene = obj["gene"]
        variant = obj["variant"]
        details = controller.details.get_details_record(gene, variant)[0]
        self.h1.SetLabel("Details for variant %s %s" % (gene, variant))
        for ctrl in self.ctrls:
            name = str(ctrl.GetName())
            label = details[name]
            ctrl.SetLabel(label)


#----------------------------------------------------------------------
class MainFrame(wx.Frame):
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="genAP wb", size=(1024, 800))
        details_panel = DetailsPanel(self)
        
        self.Show()
    def on_button(self, event):
        action = event.GetEventObject().GetName()
        print action
        return

        
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()

