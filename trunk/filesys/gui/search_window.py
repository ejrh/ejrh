import wx
import  wx.lib.mixins.listctrl  as  listmix
import sys
from holocron.filesys import Filesys
from file_dir_list import FileDirList, RevisionRootDialog


class SearchData(object):

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


class SearchPanel(wx.Panel):

    def __init__(self, 
                 parent=None, ID=-1, pos=wx.DefaultPosition,
                 size=wx.Size(800,600), style=wx.DEFAULT_FRAME_STYLE
                 ):

        title = "Filesys"
        wx.Panel.__init__(self, parent, size=(1,1))
        
        # Create the controls pane
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        controls_sizer.Add(wx.StaticText(self, -1, "Revision root"), flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.revision_root_ctrl = wx.TextCtrl(self, -1, "")
        controls_sizer.Add(self.revision_root_ctrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        b = wx.Button(self, 10, "Select...")
        controls_sizer.Add(b, flag=wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.OnClickSelect, b)
        
        controls_sizer.Add(wx.StaticText(self, -1, "Pattern"), flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.pattern_ctrl = wx.TextCtrl(self, -1, "")
        controls_sizer.Add(self.pattern_ctrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        b2 = wx.Button(self, 20, "Search")
        controls_sizer.Add(b2, flag=wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.OnClickSearch, b2)
        
        # Create the splitter between the dir tree and file list
        self.file_dir_list = FileDirList(self)
        
        # Lay out the controls
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(controls_sizer, 0, wx.ALL)
        sizer.Add(self.file_dir_list, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Initialise the data
        self.data = SearchData()
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


    def OnClickSearch(self, event):
        self.data.connect()
        
        self.data.pattern = self.pattern_ctrl.GetValue()
        
        print "search!"
