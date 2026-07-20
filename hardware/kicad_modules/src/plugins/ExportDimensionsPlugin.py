# cp D:\repos\HomeAutomation\hardware\kicad_modules\src\plugins\layout_outputs_plugin.py C:\Users\Dad\Documents\KiCad\6.0\scripting\plugins\layout_outputs_plugin.py
import os
import sys

path = os.path.realpath("C:\\Program Files\\KiCad\\6.0\\bin\\Lib\\site-packages\\")
sys.path.append(path)

from pcbnew import *

# To debug in PCBNEW console
# import os
# import sys
# path = os.path.realpath("D:\\repos\\HomeAutomation\\hardware\\kicad_modules\\src\\plugins\\")
# sys.path.append(path)

path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path)
from KicadExtensions import *


class ExportDimensionsPlugin(KicadPluginBase):
    def __init__(self):
        KicadPluginBase.__init__(self)

    def defaults(self):
        self.name = "Export Board Dimensions"
        self.category = "Mekatrol"
        self.description = "Export board edge cuts and holes"

    def Run(self):
        self.SelectLayer('Edge.Cuts')
        Refresh()


ExportDimensionsPlugin().register()
