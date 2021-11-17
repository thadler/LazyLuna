import sys
import os
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from LazyLuna.loading_functions import *
import pandas


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi('GuiDataPreparation.ui', self)
        self.ui.setWindowFlag(QtCore.Qt.CustomizeWindowHint,      True)
        self.ui.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
        self.ui.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, False)
        self.ui.setWindowFlag(QtCore.Qt.WindowMinMaxButtonsHint,  False)
        self.ui.centralwidget.setWindowState(self.ui.centralwidget.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.ui.centralwidget.activateWindow()
        
        self.ui.img_folder_btn   .clicked.connect(self.set_image_folder_path)
        self.ui.reader_folder_btn.clicked.connect(self.set_reader_folder_path)
        self.ui.load_table_btn   .clicked.connect(self.present_table)
        
        
    def set_image_folder_path(self):
        try:
            dialog = QtWidgets.QFileDialog(self, '')
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.imgs_folder_path = dialog.selectedFiles()[0]
                self.img_folder_line_edit.setText(self.imgs_folder_path)
        except Exception as e:
            print(e)
            
    def set_reader_folder_path(self):
        try:
            dialog = QtWidgets.QFileDialog(self, '')
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.reader_folder_path = dialog.selectedFiles()[0]
                self.reader_folder_line_edit.setText(self.reader_folder_path)
        except Exception as e:
            print(e)
        
    def present_table(self):
        imgs_df    = dicom_images_to_table(self.imgs_folder_path)
        study_uid  = get_study_uid(self.imgs_folder_path)
        annos_path = os.path.join(self.reader_folder_path, study_uid)
        annos_df   = annos_to_table(annos_path)
        
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        df = present_nrimages_nr_annos_table(imgs_df, annos_df, 
                                             by_series=divide_by_series_uid)
        pandas_model = DataFrameModel(df, parent=self)
        self.ui.image_information_table_view.setModel(pandas_model)


class DataFrameModel(QtCore.QAbstractTableModel):
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df=pandas.DataFrame(), parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pandas.DataFrame, fget=dataFrame, fset=setDataFrame)

    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section:int, orientation:QtCore.Qt.Orientation, role:int=QtCore.Qt.DisplayRole):
        if role==QtCore.Qt.DisplayRole:
            if orientation==QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else: return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid(): return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid(): return 0
        return self._dataframe.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
            and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt  = self._dataframe[col].dtype
        val = self._dataframe.iloc[row][col]
        if role == QtCore.Qt.DisplayRole:      return str(val)
        elif role == DataFrameModel.ValueRole: return val
        if role == DataFrameModel.DtypeRole:   return dt
        return QtCore.QVariant()

    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole:    b'display',
            DataFrameModel.DtypeRole: b'dtype',
            DataFrameModel.ValueRole: b'value'
        }
        return roles

    
def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = Window()
    gui.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()