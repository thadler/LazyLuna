# General information for Analyzer Tool loading & statistics
# saving (to excel spreadsheet), displaying (to pyqt5)

import pandas
from pandas import DataFrame
from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic
import traceback

from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


########################################################################
## For conversion from Pandas DataFrame to PyQt5 Abstract Table Model ##
########################################################################
class DataFrameModel(QtGui.QStandardItemModel):
    def __init__(self, data, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self._data = data
        for i in range(len(data.columns)):
            data_col = [QtGui.QStandardItem("{}".format(x)) for x in data.iloc[:,i].values]
            self.appendColumn(data_col)
        return
    
    def rowCount(self, parent=None): 
        return len(self._data.values)
    
    def columnCount(self, parent=None): 
        return self._data.columns.size
    
    def headerData(self, x, orientation, role):
        try:
            if orientation==QtCore.Qt.Horizontal and role==QtCore.Qt.DisplayRole: return self._data.columns[x]
            if orientation==QtCore.Qt.Vertical   and role==QtCore.Qt.DisplayRole: return self._data.index[x]
        except Exception as e: print('WARNING in DataFrameModel!!!: ', traceback.format_exc())
        return None
    
    
########################
## Custom Table Class ##
########################
class Table:
    def __init__(self):
        self.df = DataFrame()
        
    # overwrite
    def calculate(self):
        self.df = DataFrame()
        
    def store(self, path):
        pandas.DataFrame.to_csv(self.df, path, sep=';', decimal=',')
        
    def to_pyqt5_table_model(self):
        return DataFrameModel(self.df)
    
