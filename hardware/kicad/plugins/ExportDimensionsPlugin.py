# Install with ../tools/install-plugins.ps1 or copy this file into KiCad's scripting/plugins directory.
import os
import sys

path = os.path.realpath("C:\\Program Files\\KiCad\\6.0\\bin\\Lib\\site-packages\\")
sys.path.append(path)

from pcbnew import *

# To debug in PCBNEW console
# import os
# import sys
# path = os.path.realpath("../plugins")
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
