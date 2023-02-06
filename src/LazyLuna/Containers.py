import os
import traceback
from time import time
import pickle
import pydicom

from LazyLuna import loading_functions
from LazyLuna.Annotation import Annotation


########
# Case #
########
class Case:
    """Case is a container class for dicom images and annotations pertaining to a case and a reader

    Case objects offer:
        - attaching categories and clinical results
        - getters for dicoms, images, annotations

    Args:
        imgs_path (str):   path to dicom folder
        annos_path (str):  path to annotation folder
        case_name (str):   case folder name
        reader_name (str): reader name

    Attributes:
        imgs_path (str):   path to dicom folder
        annos_path (str):  path to annotation folder
        case_name (str):   case folder name
        reader_name (str): reader name
        type (str):        current view on case
        available_types (set of str): all views that have been instantiated
        all_imgs_sop2filepath (dict of str: dict of str: list of str): mapping of view type names to dict of sopinstanceuids to dicom filepaths
        studyinstanceuid (str):                unique identifier for cases
        annos_sop2filepath (dict of str: str): mapping of sopinstanceuids to annotation filepaths
        categories (list of Category):         list of category objects
        crs (list of ClinicalResult):          list of clinical result objects
    """
    
    def __init__(self, imgs_path, annos_path, case_name, reader_name, debug=False):
        if debug: st = time()
        self.imgs_path    = imgs_path
        self.annos_path   = annos_path
        self.case_name    = case_name
        self.reader_name  = reader_name
        self.type         = 'None'
        self.available_types = set()
        self.all_imgs_sop2filepath  = loading_functions.read_dcm_images_into_sop2filepaths(imgs_path, debug)
        self.studyinstanceuid       = self._get_studyinstanceuid()
        self.annos_sop2filepath     = loading_functions.read_annos_into_sop2filepaths(annos_path, debug)
        if debug: print('Initializing Case took: ', time()-st)

    def _get_studyinstanceuid(self):
        """Returns the case's studyinstanceuid
        
        Returns: 
            str: case's dicom StudyInstanceUID 
        """
        for n in self.all_imgs_sop2filepath.keys():
            for sop in self.all_imgs_sop2filepath[n].keys():
                return pydicom.dcmread(self.all_imgs_sop2filepath[n][sop], stop_before_pixels=False).StudyInstanceUID

    def attach_categories(self, categories):
        """Attaches categories to case
        
        Args:
            categories (list of Category): list of category classes 
        """
        self.categories = [] # iteratively adding categories is a speed-up
        for c in categories: self.categories.append(c(self))

    def attach_clinical_results(self, crs):
        """Attaches clinical results to case
        
        Args:
            crs (list of Clinical_Result): list of Clinical_Result classes 
        """
        self.crs = [cr(self) for cr in crs]

    # lazy loaders & getters
    def load_dcm(self, sop):
        """Loads a dicom dataset stored in dicom file format
        
        Args:
            sop (str): sopInstanceUID of dicom
            
        Returns:
            dicom dataset
        """
        return pydicom.dcmread(self.imgs_sop2filepath[sop], stop_before_pixels=False)

    def load_anno(self, sop):
        """Loads Annotation
        
        Args:
            sop (str): sopInstanceUID of annotation
            
        Returns:
            Annotation
        """
        if sop not in self.annos_sop2filepath.keys(): return Annotation(None)
        return Annotation(self.annos_sop2filepath[sop], sop)

    def get_img(self, sop, value_normalize=True, window_normalize=True):
        """Loads and normalizes an image 
        
        Args:
            sop (str): sopInstanceUID of dicom
            value_normalize (bool): whether to normalize pixel values according to dicom attribute
            window_normalize (bool): whether to normalize pixel values according to dicom attribute
            
        Returns:
            ndarray (2D array of float): img
        """
        dcm = self.load_dcm(sop)
        img = dcm.pixel_array
        if value_normalize:
            if [0x0028, 0x1052] in dcm and [0x0028, 0x1053] in dcm:
                img = img * float(dcm[0x0028, 0x1053].value) + float(dcm[0x0028, 0x1052].value)
        if window_normalize:
            minn, maxx = 0, 255
            if [0x0028, 0x1050] in dcm and [0x0028, 0x1051] in dcm:
                c = float(dcm[0x0028, 0x1050].value) # window center
                w = float(dcm[0x0028, 0x1051].value) # window width
                search_if, search_elif   = img<=(c-0.5)-((w-1)/2), img>(c-0.5)+((w-1)/2)
                img = ((img-(c-0.5)) / (w-1)+0.5) * (maxx-minn) + minn
                img[search_if]   = minn
                img[search_elif] = maxx
        return img

    def store(self, storage_dir):
        """Stores case 
        
        Args:
            storage_dir (str): path to directory into which this case is stored, NOT the storage_path. Full path is generated
            
        Returns:
            str: storage_path
        """
        if not os.path.isdir(storage_dir): print('Storage failed. Must specify a directory.'); return
        print(storage_dir)
        print(self.reader_name)
        print(self.case_name)
        print(self.studyinstanceuid)
        storage_path = os.path.join(storage_dir, self.reader_name+'_'+self.case_name+'_'+self.studyinstanceuid+'_LL_case.pickle')
        f = open(storage_path, 'wb'); pickle.dump(self, f); f.close()
        return storage_path


###################
# Case Comparison #
###################
class Case_Comparison:
    """Case_Comparison is a container class for two Cases to be compared to each other

    Args:
        case1 (LazyLuna.Containers.Case): first Case
        case2 (LazyLuna.Containers.Case): second Case
        
            
    Raise Exception: 
        When case1's studyinstanceuid != case2's studyinstanceuid

    Attributes:
        case1 (LazyLuna.Containers.Case): first Case
        case2 (LazyLuna.Containers.Case): second Case
    """
    def __init__(self, case1, case2):
        self.case1, self.case2 = case1, case2
        # assertions here? same case, same images,
        if self.case1.studyinstanceuid!=self.case2.studyinstanceuid:
            raise Exception('A Case Comparison must reference the same case: '+self.case1.case_name, self.case2.case_name, ' , StudyInstanceUIDs: ', self.case1.studyinstanceuid, self.case2.studyinstanceuid)

    def get_categories_by_type(self, cat_type):
        """Returns the categories of both cases belonging to the passed category_type
        
        Args:
            cat_type (class): Class type of Category - type(Category)
            
        Returns:
            (Category, Category): Categories of case1 and case2
        """
        cat1 = [cat for cat in self.case1.categories if isinstance(cat, cat_type)][0]
        cat2 = [cat for cat in self.case2.categories if isinstance(cat, cat_type)][0]
        return cat1, cat2

    def get_categories_by_example(self, cat_example):
        """Returns the categories of both cases of the category example
        
        Args:
            cat_example (Category): category example of which to get the exemplars of both cases
            
        Returns:
            (Category, Category): Categories of case1 and case2
        """
        return self.get_categories_by_type(type(cat_example))