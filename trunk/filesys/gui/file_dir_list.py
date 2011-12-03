import wx
import  wx.lib.mixins.listctrl  as  listmix
import sys
from holocron.filesys import Filesys

class RevisionRootDialog(wx.Dialog):

    def __init__(
            self, parent, ID, title, data, size=wx.DefaultSize, pos=wx.DefaultPosition, 
            style=wx.DEFAULT_DIALOG_STYLE,
            useMetal=False,
            ):
        
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        dir_tree_id = wx.NewId()
        self.dir_tree = DirTree(self, dir_tree_id, wx.DefaultPosition, wx.DefaultSize,
                               wx.TR_DEFAULT_STYLE | wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT)

        controls_sizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        controls_sizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        controls_sizer.AddButton(btn)
        
        controls_sizer.Realize()
        
        sizer.Add(self.dir_tree, 1, wx.EXPAND)
        sizer.Add(controls_sizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(sizer)        
        
        # populate it
        self.data = data
        self.dir_tree.hidden_root = self.dir_tree.AddRoot('hidden')
        for rev_id, root in self.data.get_all_roots():
            self.AddRoot(root)


    def AddRoot(self, root):
        r = self.dir_tree.AppendItem(self.dir_tree.hidden_root, '%s:%s' % (root.rev_id, root.name))
        self.dir_tree.SetPyData(r, root)
        root.got_subdirs = False
        root.needs_expansion = True
        root.tree_item = r
        self.dir_tree.SetItemHasChildren(r, True)
        
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.dir_tree.OnItemExpanding, self.dir_tree)
        
        self.dir_tree.SelectItem(root.tree_item)


class FileDirList(wx.SplitterWindow):

    def __init__(self, 
                 parent=None, style=wx.DEFAULT_FRAME_STYLE
                 ):

        wx.SplitterWindow.__init__(self, parent, -1, style = style)
        
        # Create the dir tree widgit
        dir_tree_id = wx.NewId()
        self.dir_tree = DirTree(self, dir_tree_id, wx.DefaultPosition, wx.DefaultSize,
                               wx.TR_DEFAULT_STYLE | wx.TR_HAS_BUTTONS)
        
        # Create the file list widgit
        file_list_panel_id = wx.NewId()
        self.file_list_panel = FileListPanel(self, file_list_panel_id)
        
        self.SplitVertically(self.dir_tree, self.file_list_panel, 200)
        self.SetMinimumPaneSize(200)


    def SetRoot(self, root, subdirs):
        self.dir_tree.DeleteAllItems()
        
        r = self.dir_tree.AddRoot(root.name)
        self.dir_tree.SetPyData(r, root)
        root.got_subdirs = True
        root.needs_expansion = False
        root.tree_item = r
        
        for item in subdirs:
            c = self.dir_tree.AppendItem(r, item.name)
            self.dir_tree.SetPyData(c, item)
            item.got_subdirs = False
            item.tree_item = c
            item.rev_id = root.rev_id
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.dir_tree)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.dir_tree.OnItemExpanding, self.dir_tree)
        self.dir_tree.Expand(r)
        
        self.dir_tree.SelectItem(root.tree_item)


    def SetCurrentDir(self, dir):
        children = self.data.filesys.get_children(dir.id)
        self.file_list_panel.PopulateList(children)


    def OnSelChanged(self, event):
        tree_item = event.GetItem()
        data = self.dir_tree.GetPyData(tree_item)
        self.SetCurrentDir(data)


class DirTree(wx.TreeCtrl):

    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)


    def OnCompareItems(self, item1, item2):
        t1 = self.GetItemText(item1)
        t2 = self.GetItemText(item2)
        if t1 < t2: return -1
        if t1 == t2: return 0
        return 1


    def OnItemExpanding(self, event):
        tree_item = event.GetItem()
        data = self.GetPyData(tree_item)
        
        try:
            if data.needs_expansion:
                subdirs = self.GetParent().data.filesys.get_subdirs(data.id)
                for item_data in subdirs:
                    c = self.AppendItem(tree_item, item_data.name)
                    self.SetPyData(c, item_data)
                    item_data.got_subdirs = False
                    item_data.rev_id = data.rev_id
                data.got_subdirs = True
                data.needs_expansion = False
        except:
            pass
        
        child, cookie = self.GetFirstChild(tree_item)
        while child.IsOk():
            data = self.GetPyData(child)
            
            if not data.got_subdirs:
                subdirs = self.GetParent().data.filesys.get_subdirs(data.id)
                for item_data in subdirs:
                    c = self.AppendItem(child, item_data.name)
                    self.SetPyData(c, item_data)
                    item_data.got_subdirs = False
                    item_data.rev_id = data.rev_id
                data.got_subdirs = True
            
            child, cookie = self.GetNextChild(tree_item, cookie)


class FileList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class FileListPanel(wx.Panel, listmix.ColumnSorterMixin):

    def __init__(self, parent, ID):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        self.ID = ID
        file_list_id = wx.NewId()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.list = FileList(self, file_list_id,
                                 style=wx.LC_REPORT 
                                 #| wx.BORDER_SUNKEN
                                 | wx.BORDER_NONE
                                 | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 #| wx.LC_NO_HEADER
                                 #| wx.LC_VRULES
                                 #| wx.LC_HRULES
                                 #| wx.LC_SINGLE_SEL
                                 )
        
        self.list.InsertColumn(0, "Name")
        self.list.InsertColumn(1, "Size", wx.LIST_FORMAT_RIGHT)
        self.list.InsertColumn(2, "Modified")
        self.list.InsertColumn(3, "Info")
        
        sizer.Add(self.list, 1, wx.EXPAND)

        # Now that the list exists we can init the other base class,
        # see wx/lib/mixins/listctrl.py
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 3)
        #self.SortListItems(0, True)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)


    def PopulateList(self, list):
        
        self.list.DeleteAllItems()
        
        i = 0
        for item in list:
            index = self.list.InsertStringItem(sys.maxint, item.name)
            self.list.SetStringItem(index, 1, '%d' % item.size)
            self.list.SetStringItem(index, 2, '%s' % item.modified)
            self.list.SetStringItem(index, 3, '%d' % item.id)
            self.list.SetItemData(i, i)
            self.itemDataMap[i] = (item.name, item.size, item.modified)
            i += 1
        
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.list.SetColumnWidth(0, self.list.GetColumnWidth(0)+4)
        
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(2, 100)

        self.currentItem = 0


    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list
