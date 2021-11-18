import sys
import os
import numpy as np
import pandas

from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic

from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)


from LazyLuna.loading_functions import *


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
        
        # folder selection
        self.ui.img_folder_btn   .clicked.connect(self.set_image_folder_path)
        self.ui.reader_folder_btn.clicked.connect(self.set_reader_folder_path)
        self.ui.load_table_btn   .clicked.connect(self.present_table)
        
        # setting LL tags
        self.ui.SAX_CINE_add_to_dict.clicked.connect(self.set_sax_cine_LL_tags)
        self.ui.SAX_CS_add_to_dict  .clicked.connect(self.set_sax_cs_LL_tags)
        self.ui.LAX_2CV_add_to_dict .clicked.connect(self.set_lax_2cv_LL_tags)
        self.ui.LAX_3CV_add_to_dict .clicked.connect(self.set_lax_3cv_LL_tags)
        self.ui.LAX_4CV_add_to_dict .clicked.connect(self.set_lax_4cv_LL_tags)
        self.ui.SAX_T1_add_to_dict  .clicked.connect(self.set_sax_T1_LL_tags)
        self.ui.SAX_T2_add_to_dict  .clicked.connect(self.set_sax_T2_LL_tags)
        self.ui.SAX_LGE_add_to_dict .clicked.connect(self.set_sax_lge_LL_tags)
        self.ui.remove_from_dict    .clicked.connect(self.remove_LL_tags)
        
        # adding tags to dicoms
        self.ui.store_LL_Tags.clicked.connect(self.store_LL_tags)
        
        self.ui.image_information_table_view.doubleClicked.connect(self.show_dcms)
        
        # adding figure
        self.DCM_MplWidget.canvas.axes.clear()
        self.DCM_MplWidget.canvas.axes.imshow(np.arange(25**2).reshape(25,25))
        self.DCM_MplWidget.canvas.axes.set_title('DCMs')
        self.DCM_MplWidget.canvas.draw()
        self.DCM_MplWidget.canvas.mpl_connect('key_press_event', 
                                        self.DCM_MplWidget.keyPressEvent)
        
        
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
        self.key2LLtag = dict()
        self.imgs_df   = dicom_images_to_table(self.imgs_folder_path)
        study_uid      = get_study_uid(self.imgs_folder_path)
        try:
            annos_path       = os.path.join(self.reader_folder_path, study_uid)
            annos_df         = annos_to_table(annos_path)
        except: annos_df     = None
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        if annos_df is not None:
            self.information_df = present_nrimages_nr_annos_table(self.imgs_df, 
                                          annos_df, by_series=divide_by_series_uid)
        else:
            self.information_df = present_nrimages_table(self.imgs_df, 
                                                 by_series=divide_by_series_uid)
        pandas_model = DataFrameModel(self.information_df, parent=self)
        self.ui.image_information_table_view.setModel(pandas_model)

    def set_sax_cine_LL_tags(self): self.set_LL_tags('Lazy Luna: SAX CINE')
    def set_sax_cs_LL_tags(self):   self.set_LL_tags('Lazy Luna: SAX CS')
    def set_lax_2cv_LL_tags(self):  self.set_LL_tags('Lazy Luna: LAX 2CV')
    def set_lax_3cv_LL_tags(self):  self.set_LL_tags('Lazy Luna: LAX 3CV')
    def set_lax_4cv_LL_tags(self):  self.set_LL_tags('Lazy Luna: LAX 4CV')
    def set_sax_T1_LL_tags(self):   self.set_LL_tags('Lazy Luna: SAX T1')
    def set_sax_T2_LL_tags(self):   self.set_LL_tags('Lazy Luna: SAX T2')
    def set_sax_lge_LL_tags(self):  self.set_LL_tags('Lazy Luna: SAX LGE')
    def remove_LL_tags(self):       self.set_LL_tags('Lazy Luna: None')
    
    def store_LL_tags(self): add_and_store_LL_tags(self.imgs_df, self.key2LLtag)
        
    def set_LL_tags(self, name):
        table = self.ui.image_information_table_view
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        idxs  = table.selectionModel().selectedIndexes()
        for idx in sorted(idxs):
            if not divide_by_series_uid: 
                value = table.model().index(idx.row(), 0).data()
            else: 
                value = (table.model().index(idx.row(), 0).data(), table.model().index(idx.row(), 1).data())
            self.key2LLtag[value] = name
            self.information_df.at[idx.row(),'Change LL_tag'] = name
        pandas_model = DataFrameModel(self.information_df, parent=self)
        self.ui.image_information_table_view.setModel(pandas_model)
        #print('key2LLtag: ', self.key2LLtag)
        

    def show_dcms(self, modelindex):
        row   = modelindex.row()
        table = self.ui.image_information_table_view
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        series_description = self.information_df.at[row,'series_descr']
        if divide_by_series_uid:
            series_uid = self.information_df.at[row,'series_uid']
        else: series_uid = None
        paths = get_img_paths_for_series_descr(self.imgs_df, series_description, 
                                               series_uid)
        self.DCM_MplWidget.set_dcms([pydicom.dcmread(p) for p in paths])
        
    


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