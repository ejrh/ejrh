import sys
import wx
import wx.aui

sys.path.append('../../..')

from browser_window import BrowserPanel
from comparison_window import ComparisonPanel
from search_window import SearchPanel


class MainFrame(wx.Frame):

    def __init__(self, 
                 parent=None, ID=-1, pos=wx.DefaultPosition,
                 size=wx.Size(800,600), style=wx.DEFAULT_FRAME_STYLE
                 ):

        title = "Filesys"
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        
        # Menu bar
        menu_bar = wx.MenuBar()

        # 1st menu from left
        file_menu = wx.Menu()
        new_submenu = wx.Menu()
        new_submenu.Append(111, "&Browser", "Browse a Filesys revision")
        new_submenu.Append(112, "&Comparison", "Compare two Filesys revisions")
        new_submenu.Append(113, "&Search", "Search for files in Filesys")
        new_submenu.Append(114, "&Import", "Import a new Filesys revision")
        file_menu.AppendMenu(101, "&New", new_submenu)
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit", "Exit this program")

        menu_bar.Append(file_menu, "&File")
        
        self.Bind(wx.EVT_MENU, self.OnNewBrowser, id=111)
        self.Bind(wx.EVT_MENU, self.OnNewComparison, id=112)
        self.Bind(wx.EVT_MENU, self.OnNewSearch, id=113)
        self.Bind(wx.EVT_MENU, self.OnNewImport, id=114)
        
        self.Bind(wx.EVT_MENU, self.OnFileExit, id=wx.ID_EXIT)

        self.SetMenuBar(menu_bar)
        
        # Status bar
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar")
        
        # Notebook for windows
        self.nb = wx.aui.AuiNotebook(self)
        self.OnNewBrowser(None)
        
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)


    def OnNewBrowser(self, event):
        page = BrowserPanel(self.nb, -1)
        self.nb.AddPage(page, "Browser", True)


    def OnNewComparison(self, event):
        page = ComparisonPanel(self.nb, -1)
        self.nb.AddPage(page, "Comparison", True)


    def OnNewSearch(self, event):
        page = SearchPanel(self.nb, -1)
        self.nb.AddPage(page, "Search", True)


    def OnNewImport(self, event):
        page = ImportPanel(self.nb, -1)
        self.nb.AddPage(page, "Import", True)


    def OnFileExit(self, event):
        self.Close()


class MainApp(wx.App):

    def OnInit(self):
        self.SetAppName("Filesys")
        
        frame = MainFrame()
        frame.Show(True)

        return True


def main():
    app = MainApp(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
