from pcbnew import *


class KicadPluginBase(ActionPlugin):
    def __init__(self):
        ActionPlugin.__init__(self)
        self.board = GetBoard()
        self.IndexLayers()

    def IndexLayers(self):
        self.layers = {}
        i = PCBNEW_LAYER_ID_START
        while i < PCBNEW_LAYER_ID_START + PCB_LAYER_ID_COUNT:
            self.layers[BOARD_GetStandardLayerName(i)] = i
            i += 1

    def SelectLayer(self, layerName):
        if layerName in self.layers.keys():
            layerId = self.layers[layerName]
            self.board.SetLayer(layerId)
            print(f"Layer set to '{layerName}'")
        else:
            print(f"Layer name '{layerName}' does not exist")
