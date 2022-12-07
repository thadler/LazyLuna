import os
from matplotlib.figure import Figure

class Visualization(Figure):
    """Table is a class for LazyLuna's visualizations

    Table offers:
        - simple integration into PyQt5
        - keyPressEvent and MouseClick interaction with the figures
    """
    def __init__(self):
        super().__init__()
        pass
    
    def visualize(self):
        """Overwrite this method for the visualization calculation"""
        pass
    
    def keyPressEvent(self, event):
        """Overwrite this method for keyPressEvents"""
        pass

    # overwrite figure name
    def store(self, storepath, figurename='visualization.png'):
        """Overwrite this method for Figure storage"""
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)
