from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.SaxT1PreView import SAX_T1_PRE_View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class SAX_T1_POST_View(SAX_T1_PRE_View):
    def __init__(self):
        super().__init__()
        self.name   = 'SAX T1 POST'
        self.ll_tag = 'SAX T1 POST'
        self.cmap = 'gray'
    
    def customize_case(self, case, debug=False):
        if debug:
            print('starting customize t1: ', case.case_name)
            st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath[self.ll_tag]
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([SAX_T1_Category])
            case.other_categories[self.ll_tag] = case.categories
        else:
            if self.ll_tag in case.other_categories.keys(): case.categories = case.other_categories[self.ll_tag]
            else: case.attach_categories([SAX_T1_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([SAXMap_GLOBALT1_POST, NR_SLICES])
        # set new type
        case.type = self.ll_tag
        if debug: 
            print('Customization in SAX T1 POST view took: ', time()-st)
            print('ending customize: ', case.case_name)
        return case