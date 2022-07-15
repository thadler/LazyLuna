from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QComboBox, QHeaderView, QLabel, QFileDialog, QDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import pyqtSlot

import sys
import os
import pickle
import pydicom
import numpy as np
from pathlib import Path
from pandas import DataFrame
import traceback

from catch_converter.parse_contours import parse_cvi42ws
from LazyLuna.Mini_LL import *
from LazyLuna.utils   import *
from LazyLuna.Tables  import *
from LazyLuna.Figures import *
from LazyLuna.loading_functions import *

class Module(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title  = 'Dirty Dobbys Fat Fraction Tool'
        shift       = 30
        self.left   = 0
        self.top    = shift
        self.width  = 1200
        self.height = 800  + shift
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.table_widget = MyTabWidget(self)
        self.setCentralWidget(self.table_widget)
        self.show()
    
class MyTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        # Closable Tabs
        #self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda index: self.tabs.removeTab(index))
        # Add tabs
        self.tabs.addTab(self.tab1, "Tab1")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        
        # choose dcms path
        self.imgs_folder_button = QPushButton('Select Imgs Folder')
        self.imgs_folder_button.clicked.connect(self.set_dcms_folder)
        self.tab1.layout.addWidget(self.imgs_folder_button, 0, 0)
        self.imgs_folder_path = QLineEdit('')
        self.tab1.layout.addWidget(self.imgs_folder_path, 1, 0)
        
        # choose annos path
        self.annos_folder_button = QPushButton('Select WS Folder')
        self.annos_folder_button.clicked.connect(self.set_annos_folder)
        self.tab1.layout.addWidget(self.annos_folder_button, 2, 0)
        self.annos_folder_path = QLineEdit('')
        self.tab1.layout.addWidget(self.annos_folder_path, 3, 0)
        
        
        
        # choose output path
        self.out_folder_button = QPushButton('Select Output Folder')
        self.out_folder_button.clicked.connect(self.set_output_folder)
        self.tab1.layout.addWidget(self.out_folder_button, 5, 0)
        self.out_folder_path = QLineEdit('')
        self.tab1.layout.addWidget(self.out_folder_path, 6, 0)
        
        
        #load button
        self.button_load = QPushButton("Load Stuff")
        self.button_load.clicked.connect(self.load_stuff)
        self.tab1.layout.addWidget(self.button_load, 7, 0)
        
        # Visualization
        self.figure = FFMapVisualization()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('key_press_event', self.figure.keyPressEvent)
        self.canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas.setFocus()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.tab1.layout.addWidget(self.canvas,  0, 1, 12,1)
        self.tab1.layout.addWidget(self.toolbar, 13,1, 1, 1)
        
        
        # set table view
        #self.caseTableView = QTableView()
        #self.tab1.layout.addWidget(self.caseTableView, 0, 1, 10,1)
        self.tab1.setLayout(self.tab1.layout)
        self.tab1.layout.setColumnStretch(1, 2)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
    def set_dcms_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                path = dialog.selectedFiles()[0]
                self.imgs_folder_path.setText(path)
                self.set_relevant_paths()
        except Exception as e:
            print('Setting Images path failed: ', e)
            print(traceback.format_exc())
    
    def set_annos_folder(self): 
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                path = dialog.selectedFiles()[0]
                self.annos_folder_path.setText(path)
            parse_cvi42ws(path, path, process=True, debug=False)
            self.set_relevant_paths()
        except Exception as e:
            print('Setting Anno path failed: ', e)
            print(traceback.format_exc())
            
            
    def set_relevant_paths(self):
        try:
            path1 = self.imgs_folder_path.text()
            path2 = self.annos_folder_path.text()
            parent_path = str(Path(path1).parent.absolute())
            if path1=='' or path2=='': return
            paths = get_imgs_and_annotation_paths(parent_path, path2)
            self.imgs_path, self.annos_path = [p for p in paths if path1 in p[0]][0]
            print('FOLDERS: ', self.imgs_path, self.annos_path)
        except Exception as e:
            print('Setting relevant paths failed: ', e)
            print(traceback.format_exc())
            
    def set_output_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                path = dialog.selectedFiles()[0]
                self.out_folder_path.setText(path)
        except Exception as e:
            print('Setting Output path failed: ', e)
            print(traceback.format_exc())
        
    def load_stuff(self):
        try:
            imgs_path  = self.imgs_path
            annos_path = self.annos_path
            out_path   = self.out_folder_path.text()
        except Exception as e:
            print('Failed setting fields: ', e)
            print(traceback.format_exc())
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("*Breaks into Tears* You're so gracious, Miss!\n")
            text = "Paths were not selected:\n" + str(traceback.format_exc())
            error_dialog.setInformativeText(text)
            error_dialog.setWindowTitle("Error")
            error_dialog.exec_()

        try:
            # load annos
            annos = [Annotation(os.path.join(annos_path,a), a.replace('.pickle','')) for a in os.listdir(annos_path) if 'case' not in a]
            annos = {a.sop:a for a in annos}
            sops  = [a.sop for a in annos.values()]
            print('Loaded Annos')
            
            print('Loading Images')
            dcms    = []
            dcms_ff = []
            for ip, p in enumerate(Path(imgs_path).glob('**/*.dcm')):
                try:
                    p = str(p)
                    dcm = pydicom.dcmread(p, stop_before_pixels=True)
                    if dcm.SOPInstanceUID in sops:
                        dcm = pydicom.dcmread(p, stop_before_pixels=False)
                        dcms.append(dcm)
                    if '_W_FF' in dcm.SeriesDescription and 'rs3dt2d' in dcm.SeriesDescription:
                        dcm = pydicom.dcmread(p, stop_before_pixels=False)
                        dcms_ff.append(dcm)
                except:
                    pass
            dcms     = {dcm.SOPInstanceUID:dcm for dcm in dcms}
            dcms_ff  = sorted(dcms_ff, key=lambda x: float(x.SliceLocation))
            dcms_tmp = dict()
            for sop in dcms.keys():
                dcm = dcms[sop]
                slloc = dcm.SliceLocation
                for dcm2 in dcms_ff:
                    if dcm2.SliceLocation==slloc:
                        dcms_tmp[sop] = dcm2
            dcms_ff = dcms_tmp
            print('Loaded Images')


        except Exception as e:
            print('Failed Loading Images or Annotations: ', e)
            print(traceback.format_exc())
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("*Irons Fingers* Bad House Elf!\n")
            text = "I always knew you were a grand wizard..."
            text += "\nI failed to load images or annotations. Are they there:\n" + str(traceback.format_exc())
            error_dialog.setInformativeText(text)
            error_dialog.setWindowTitle("Error")
            error_dialog.exec_()

        try: 
            # Store Tables and Category
            cat = FF_Category(dcms, dcms_ff, annos)
            store_path = os.path.join(out_path, os.path.basename(self.imgs_folder_path.text()))
            cat.store_tables(store_path=store_path)
            cat_store_path = store_path+'_category.pickle'
            pickle.dump(cat, open(cat_store_path, 'wb'), pickle.HIGHEST_PROTOCOL)
            
            self.figure.set_category(cat)
            self.figure.set_canvas(self.canvas)
            self.figure.visualize()
        
        except Exception as e:
            print('Failed Loading Stuff: ', e)
            print(traceback.format_exc())
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("*Bangs Head*\n Bad Dobby! Bad Dobby!")
            text = "I'm sorry, Harry Potter, sir!"
            text += "\nI was unable to load certain FF images or store the data. Slices may be missing:\n" + str(e)
            error_dialog.setInformativeText(text)
            error_dialog.setWindowTitle("Error")
            error_dialog.exec_()
        

class FF_Category:
    def __init__(self, dcms_fat, dcms_ff, annos):
        self.dcms_fat  = dcms_fat 
        self.dcms_ff   = dcms_ff
        self.annos     = annos
        self.depth2sop = self.sort_sops_2_depth(dcms_fat)
        self.nr_slices = len(self.depth2sop.values())
        self.set_params()
        
    def set_params(self):
        dcm1, dcm2 = self.get_fat_dcm(0), self.get_fat_dcm(1)
        self.slice_thickness = dcm1.SliceThickness
        self.spacing_between_slices = np.abs(dcm1.SliceLocation - dcm2.SliceLocation)
        self.ph, self.pw = dcm1.PixelSpacing
        
    def sort_sops_2_depth(self, dcms):
        sl_locs = [(dcm.SOPInstanceUID, float(dcm.SliceLocation)) for dcm in dcms.values()]
        sl_locs = sorted(sl_locs, key=lambda x:x[1])
        depth2sop = {i:x[0] for i,x in enumerate(sl_locs)}
        return depth2sop
        
    def get_fat_dcm(self, depth): return self.dcms_fat[self.depth2sop[depth]]
    def get_ff_dcm (self, depth): return self.dcms_ff[self.depth2sop[depth]]
    def get_fat_img(self, depth): return self.get_fat_dcm(depth).pixel_array
    def get_ff_img (self, depth): return self.get_ff_dcm(depth).pixel_array
    def get_anno   (self, depth): return self.annos[self.depth2sop[depth]]
    
    def get_ff_in_myo(self, depth):
        ff_cont = utils.to_polygon(self.get_ff_img(depth))
        anno = self.get_anno(depth)
        pixels_inside_myo = anno.get_contour('lv_myo').intersection(ff_cont)
        pixels_inside_myo = utils.geometry_collection_to_Polygon(pixels_inside_myo)
        return pixels_inside_myo
    
    # in ml
    def get_ff_volume(self):
        dcm_tmp = self.get_ff_dcm(0)
        ph, pw = self.ph, self.pw
        annos = [self.get_ff_in_myo(d) for d in range(self.nr_slices)]
        areas = [self.get_ff_in_myo(d).area for d in range(self.nr_slices)]
        has_conts = [a!=0 for a in areas]
        top_idx, bot_idx  = has_conts.index(True), self.nr_slices-has_conts[::-1].index(True)-1
        total_vol = 0
        for d in range(self.nr_slices):
            area = self.get_ff_in_myo(d).area
            pd   = (self.slice_thickness+self.spacing_between_slices)/2 if d in [top_idx, bot_idx] else self.spacing_between_slices
            total_vol += ph * pw * pd * area
        return total_vol / 1000
    
    # in ml
    def get_fat_volume(self):
        dcm_tmp = self.get_fat_dcm(0)
        ph, pw = self.ph, self.pw
        annos = [self.get_anno(d) for d in range(self.nr_slices)]
        areas = [a.get_contour('lv_myo').area if a is not None else 0.0 for a in annos]
        has_conts = [a!=0 for a in areas]
        top_idx, bot_idx  = has_conts.index(True), self.nr_slices-has_conts[::-1].index(True)-1
        total_vol = 0
        for d in range(self.nr_slices):
            anno = self.get_anno(d)
            area = anno.get_contour('lv_myo').area - anno.get_contour('rv_pamu').area
            pd   = (self.slice_thickness+self.spacing_between_slices)/2 if d in [top_idx, bot_idx] else self.spacing_between_slices
            total_vol += ph * pw * pd * area
        return total_vol / 1000
    
    def get_area_table(self):
        rows = []
        ph, pw = self.ph, self.pw
        pd = self.spacing_between_slices
        for d in range(self.nr_slices):
            anno = self.get_anno(d)
            area1 = ph*pw*(anno.get_contour('lv_myo').area - anno.get_contour('rv_pamu').area)
            area2 = ph*pw*self.get_ff_in_myo(d).area
            vol1  = pd * area1
            rows.append([area1, pd*area1/1000, area2, pd*area2/1000])
        cols = ['Fat Areas [mm^2]', 'Fat Volume [ml]', 'FF Areas [mm^2]', 'FF Volume [ml]']
        return DataFrame(rows, columns=cols)
    
    def get_cr_table(self):
        rows = [[self.get_fat_volume(), self.get_ff_volume()]]
        cols = ['Fat Volume [ml]', 'FF Volume [ml]']
        return DataFrame(rows, columns=cols)
    
    def store_tables(self, store_path):
        try:
            df   = self.get_cr_table()
            path = store_path+'_clinical_result.csv'
            pandas.DataFrame.to_csv(df, path, sep=';', decimal=',')
            print('Clinical Results stored to: ', path)
            df   = self.get_area_table()
            path = store_path+'_areas.csv'
            pandas.DataFrame.to_csv(df, path, sep=';', decimal=',')
            print('Areas stored to: ', path)
        except Exception as e:
            print('Storing Tables failed: ', e)
            print(traceback.format_exc())


class FFMapVisualization(Figure):
    def __init__(self):
        super().__init__()
        pass
    
    def set_category(self, cat):
        self.cat = cat
        self.d   = 0
        self.h, self.w = cat.get_fat_img(0).shape
        self.add_annotation = True
        
    def set_canvas(self, canvas):
        self.canvas = canvas
    
    def visualize(self):
        cat    = self.cat
        d      = self.d
        ph, pw = self.cat.ph, self.cat.pw
        extent = (0, self.w, self.h, 0)
        axes   = self.subplots(1, 3)
        axes[0].get_shared_x_axes().join(*axes)
        axes[0].get_shared_y_axes().join(*axes)
        for ax in axes: ax.axis('off')
        axes[0].imshow(cat.get_fat_img(d), cmap='gray', extent=extent)
        axes[1].imshow(cat.get_ff_img(d) , cmap='gray', extent=extent)
        axes[2].imshow(cat.get_ff_img(d) , cmap='gray', extent=extent)
        anno = cat.get_anno(d)
        if self.add_annotation:
            self.suptitle('Slice: ' + str(d))
            anno.plot_contour_face(axes[0], 'lv_myo')
            anno.plot_contour_face(axes[0], 'rv_pamu', 'b')
            anno.plot_contour_face(axes[1], 'lv_myo')
            #anno.plot_contour_face(axes[1], 'rv_pamu', 'b')
            ff_pixel_polygon = cat.get_ff_in_myo(d)
            utils.plot_outlines(axes[2], ff_pixel_polygon, 'r')
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
    
    def keyPressEvent(self, event):
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : self.d = (self.d-1) % self.cat.nr_slices
        if event.key == 'down' : self.d = (self.d+1) % self.cat.nr_slices
        self.visualize()
        
def main():
    app = QApplication(sys.argv)
    ex = Module()    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()