import sys
import os
import numpy as np
import pandas

from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic

from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)

from catch_converter.parse_contours import parse_cvi42ws
from LazyLuna.loading_functions import *
from LazyLuna.Mini_LL import *
from LazyLuna.Tables import DataFrameModel
from LazyLuna.Guis.GuiDataPreparation import Gui_Data_Preparation2


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui = Gui_Data_Preparation2.Ui_MainWindow()
        self.ui.setupUi(self)
        #self.ui = uic.loadUi(filename, self)
        #self.ui.setWindowFlag(QtCore.Qt.CustomizeWindowHint,      True)
        #self.ui.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
        #self.ui.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, False)
        #self.ui.setWindowFlag(QtCore.Qt.WindowMinMaxButtonsHint,  False)
        self.ui.centralwidget.setWindowState(self.ui.centralwidget.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.ui.centralwidget.activateWindow()
        
        ########
        # Tab1 #
        ########
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
        
        # show dicom images for row in table
        self.ui.image_information_table_view.doubleClicked.connect(self.show_dcms)
        
        ########
        # Tab2 #
        ########
        # adding figure
        self.ui.DCM_MplWidget.canvas.axes.clear()
        self.ui.DCM_MplWidget.canvas.axes.set_title('Dicoms')
        self.ui.DCM_MplWidget.canvas.draw()
        self.ui.DCM_MplWidget.canvas.mpl_connect('key_press_event', self.ui.DCM_MplWidget.keyPressEvent)
        
        ########
        # Tab3 #
        ########
        # folder selection
        self.ui.case_img_folder_btn        .clicked.connect(self.set_case_image_folder_path)
        self.ui.case_reader_folder_btn     .clicked.connect(self.set_case_reader_folder_path)
        self.ui.cases_folder_btn           .clicked.connect(self.set_cases_folder_path)
        self.ui.case_transform_btn         .clicked.connect(self.transform_case)
        self.ui.bulk_case_images_folder_btn.clicked.connect(self.set_bulk_case_images_folder_path)
        self.ui.bulk_cases_transform_btn   .clicked.connect(self.bulk_transform_cases)
        
        
    def set_image_folder_path(self):
        try:
            dialog = QtWidgets.QFileDialog(self, '')
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.imgs_folder_path = dialog.selectedFiles()[0]
                self.ui.img_folder_line_edit.setText(self.imgs_folder_path)
        except Exception as e: print(e)
            
    def set_reader_folder_path(self):
        try:
            dialog = QtWidgets.QFileDialog(self, '')
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.reader_folder_path = dialog.selectedFiles()[0]
                self.ui.reader_folder_line_edit.setText(self.reader_folder_path)
                parse_cvi42ws(self.reader_folder_path, 
                              self.reader_folder_path, process=True, debug=False)
        except Exception as e: print(e)
            
            
    def set_case_image_folder_path(self):
        try:
            dialog = QtWidgets.QFileDialog(self, '')
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.ui.case_imgs_folder_path = dialog.selectedFiles()[0]
                self.case_img_folder_line_edit.setText(self.case_imgs_folder_path)
        except Exception as e: print(e)
            
    def set_case_reader_folder_path(self):
        try:
            dialog = QtWidgets.QFileDialog(self, '')
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.case_reader_folder_path = dialog.selectedFiles()[0]
                self.ui.case_reader_folder_line_edit.setText(self.case_reader_folder_path)
                parse_cvi42ws(self.case_reader_folder_path, 
                              self.case_reader_folder_path, process=True, debug=False)
        except Exception as e: print(e)
            
    def set_cases_folder_path(self):
        #try:
        dialog = QtWidgets.QFileDialog(self, '')
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.ui.cases_folder_path = dialog.selectedFiles()[0]
            self.ui.cases_folder_line_edit.setText(self.ui.cases_folder_path)
        #except Exception as e: print(e)
            
    def set_bulk_case_images_folder_path(self):
        #try:
        dialog = QtWidgets.QFileDialog(self, '')
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.ui.bulk_case_images_folder_path = dialog.selectedFiles()[0]
            self.ui.bulk_case_img_folder_line_edit.setText(self.ui.bulk_case_images_folder_path)
        #except Exception as e: print(e)
        
    def bulk_transform_cases(self):
        bp_imgs  = self.ui.bulk_case_images_folder_path
        bp_annos = self.case_reader_folder_path
        bp_cases = self.ui.cases_folder_path
        imgsanno_paths = get_imgs_and_annotation_paths(bp_imgs, bp_annos)
        cases = []
        sax_cine_view = SAX_CINE_View()
        sax_cs_view   = SAX_CS_View()
        for imgp, annop in imgsanno_paths:
            self.case_conversion_text_edit.append('Image and Annotation paths:/n'+imgp+'/n'+annop)
            if not os.path.exists(annop): 
                self.case_conversion_text_edit.append('No annotations: '+annop)
                continue
            case = Case(imgp, annop, os.path.basename(imgp), os.path.basename(bp_annos))
            try: 
                case = sax_cine_view.initialize_case(case)
                self.case_conversion_text_edit.append('CINE view worked for: '+case.case_name)
            except Exception as e: 
                self.case_conversion_text_edit.append('Failed at CINE view: '+str(e))
            try:
                case = sax_cs_view.initialize_case(case)
                self.case_conversion_text_edit.append('CS view worked for: '+case.case_name)
            except Exception as e: 
                self.case_conversion_text_edit.append('Failed at CS view: '+str(e))
            case.store(bp_cases)
    
    def transform_case(self):
        single_imgs_path = self.case_imgs_folder_path
        bp_annos = self.case_reader_folder_path
        bp_cases = self.cases_folder_path
        print('head: ', os.path.split(single_imgs_path)[0])
        imgsanno_paths = get_imgs_and_annotation_paths(os.path.split(single_imgs_path)[0], bp_annos)
        cases = []
        sax_cine_view = SAX_CINE_View()
        sax_cs_view   = SAX_CS_View()
        for imgp, annop in imgsanno_paths:
            if single_imgs_path not in imgp: continue
            print('Image path: ', imgp)
            self.case_conversion_text_edit.append('\nImage and Annotation paths:/n'+imgp+'/n'+annop)
            if not os.path.exists(annop): 
                self.case_conversion_text_edit.append('No annotations: '+annop)
                continue
            case = Case(imgp, annop, os.path.basename(imgp), os.path.basename(bp_annos))
            try: 
                case = sax_cine_view.customize_case(case)
                self.case_conversion_text_edit.append('CINE view worked for: '+case.case_name)
            except Exception as e: 
                self.case_conversion_text_edit.append('Failed at CINE view: '+str(e))
            try:
                case = sax_cs_view.customize_case(case)
                self.case_conversion_text_edit.append('CS view worked for: '+case.case_name)
            except Exception as e: 
                self.case_conversion_text_edit.append('Failed at CS view: '+str(e))
            case.store(bp_cases)
            #cases.append(case)
        
        
    def present_table(self):
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
    
    def set_LL_tags(self, name):
        table = self.ui.image_information_table_view
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        idxs  = table.selectionModel().selectedIndexes()
        for idx in sorted(idxs):
            self.information_df.at[idx.row(),'Change LL_tag'] = name
        pandas_model = DataFrameModel(self.information_df, parent=self)
        self.ui.image_information_table_view.setModel(pandas_model)
        
    def store_LL_tags(self):
        self.key2LLtag = self.set_key2LLtag()
        add_and_store_LL_tags(self.imgs_df, self.key2LLtag)
        
    def set_key2LLtag(self):
        key2LLtag = dict()
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        columns = ['series_descr', 'series_uid', 'Change LL_tag'] if divide_by_series_uid else ['series_descr', 'Change LL_tag']
        rows = self.information_df[columns].to_dict(orient='split')['data']
        for r in rows: key2LLtag[tuple(r[:-1])] = r[-1]
        return key2LLtag

    def show_dcms(self, modelindex):
        row   = modelindex.row()
        table = self.ui.image_information_table_view
        divide_by_series_uid = self.ui.differentiation_radio_btn.isChecked()
        series_description = self.information_df.at[row,'series_descr']
        if divide_by_series_uid:
            series_uid = self.information_df.at[row,'series_uid']
        else: series_uid = None
        paths = get_img_paths_for_series_descr(self.imgs_df, series_description, series_uid)
        self.ui.DCM_MplWidget.set_dcms([pydicom.dcmread(p) for p in paths])
        
    



    
def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = Window()
    gui.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()