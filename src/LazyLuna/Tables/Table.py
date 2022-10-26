# General information for Analyzer Tool loading & statistics
# saving (to excel spreadsheet), displaying (to pyqt5 - class below)

import pandas
from pandas import DataFrame
from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic
import traceback

from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *

    
########################
## Custom Table Class ##
########################
class Table:
    """Table is a class for LazyLuna's tabular data

    Table offers:
        - tabular data as pandas.DataFrame objects     (as attr self.df)
        - storing this data as csv spreadsheets        (as function self.store(str: path))
        - presenting tabular data in pyqt5 table views (as function self.to_pyqt5_table_model())

    Attributes:
        df (pandas.DataFrame): tabular data
    """
    def __init__(self):
        self.df = DataFrame()
        
    # overwrite
    def calculate(self):
        """overwrite this function to calculate the table and set the Table's pandas.DataFrame"""
        self.df = DataFrame()
        
    def store(self, path):
        """overwrite this function to store the Table's pandas.DataFrame (.df)"""
        pandas.DataFrame.to_csv(self.df, path, sep=';', decimal=',')
        
    def to_pyqt5_table_model(self):
        """Provides interface for PyQt5"""
        return DataFrameModel(self.df)
    



########################################################################
## For conversion from Pandas DataFrame to PyQt5 Abstract Table Model ##
########################################################################
class DataFrameModel(QtGui.QStandardItemModel):
    """Interface class to PyQt5 

    Attributes:
        _data (pandas.DataFrame): tabular data
    """
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
    