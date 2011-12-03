import wx
import  wx.lib.mixins.listctrl  as  listmix
import sys
from holocron.filesys import Filesys
from file_dir_list import FileDirList, RevisionRootDialog


class ComparisonData(object):

    def __init__(self):
        self.filesys = None


    def connect(self):
        self.filesys = Filesys()
        self.filesys.connect()


    def get_latest_root(self):
        self.current_rev = self.filesys.get_latest_rev();
        self.current_root = self.filesys.get_root(self.current_rev)
        
        subdirs = self.filesys.get_subdirs(self.current_root.id)
        
        return self.current_rev,self.current_root,subdirs


class ComparisonPanel(wx.Panel):

    def __init__(self, 
                 parent=None, ID=-1, pos=wx.DefaultPosition,
                 size=wx.Size(800,600), style=wx.DEFAULT_FRAME_STYLE
                 ):

        title = "Filesys"
        wx.Panel.__init__(self, parent, size=(1,1))
        
        # Create the controls panes
        controls_sizer1 = wx.BoxSizer(wx.HORIZONTAL)

        controls_sizer1.Add(wx.StaticText(self, -1, "First revision root"), flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.revision_root_ctrl1 = wx.TextCtrl(self, -1, "")
        controls_sizer1.Add(self.revision_root_ctrl1, flag=wx.ALIGN_CENTER_VERTICAL)
        
        b1 = wx.Button(self, 101, "Select...")
        controls_sizer1.Add(b1, flag=wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.OnClickSelect, b1)
        
        controls_sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        controls_sizer2.Add(wx.StaticText(self, -1, "Second revision root"), flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.revision_root_ctrl2 = wx.TextCtrl(self, -1, "")
        controls_sizer2.Add(self.revision_root_ctrl2, flag=wx.ALIGN_CENTER_VERTICAL)
        
        b2 = wx.Button(self, 102, "Select...")
        controls_sizer2.Add(b2, flag=wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.OnClickSelect, b2)
        
        # Create the splitter between the dir tree and file list
        self.file_dir_list = FileDirList(self)
        
        # Lay out the controls
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(controls_sizer1, 0, wx.ALL)
        sizer.Add(controls_sizer2, 0, wx.ALL)
        sizer.Add(self.file_dir_list, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Initialise the data
        self.data = ComparisonData()
        self.file_dir_list.data = self.data


    def OnClickSelect(self, event):
        self.data.connect()
        
        dlg = RevisionRootDialog(self, -1, "Select revision root", self.data, size=(350, 200),
                         style=wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME | wx.DEFAULT_DIALOG_STYLE
                         )
        dlg.CenterOnScreen()

        val = dlg.ShowModal()
        if val != wx.ID_OK:
            return
        
        tree_item = dlg.dir_tree.GetSelection()
        item = dlg.dir_tree.GetPyData(tree_item)

        rev_id  = item.rev_id
        root = item
        subdirs = self.data.filesys.get_subdirs(root.id)
        
        self.file_dir_list.SetRoot(root, subdirs)
        
        self.revision_root_ctrl.SetValue('%s:%s' % (rev_id, root.name))
