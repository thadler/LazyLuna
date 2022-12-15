from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import *

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback

import csv
import PIL


class SAX_LGE_View(View):
    def __init__(self):
        self.load_categories()
        # contour names with scars
        self.contour_names = ['lv_myo', 'lv_endo', 'scar', 'noreflow']
        for exclude in [False, True]:
            cont_name = 'scar_fwhm' + ('_excluded_area' if exclude else '')
            self.contour_names += [cont_name]
        self.contour2categorytype = {cname:self.all for cname in self.contour_names}
        
        # register tabs here:
        import LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab          as tab1
        import LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_tab as tab2
        import LazyLuna.Guis.Addable_Tabs.CC_Overview_Tab         as tab4
        
        self.case_tabs  = {'Metrics and Figure': tab1.CC_Metrics_Tab, 'Clinical Results and Images': tab4.CC_CRs_Images_Tab}
        self.stats_tabs = {'Clinical Results'  : tab2.CCs_ClinicalResults_Tab}
        
    def load_categories(self):
        self.all = [SAX_LGE_Category]

    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, cvi_preprocess=True, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX LGE']
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_LGE_Category])
        # A SCAR calculating preprocessing step is necessary for LGE
        if debug: st_preprocess = time()
        cat = case.categories[0]
        if cvi_preprocess:
            cat.preprocess_scars()
        if debug: print('Calculating scars took: ', time()-st_preprocess)
        if debug: print('Set of anno keys are: ', list(set([akey for a in cat.get_annos() for akey in a.anno.keys()])))
        case.other_categories['SAX LGE'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        
        # set new type
        case.type = 'SAX LGE'
        case.available_types.add('SAX LGE')
        if debug: print('Customization in SAX LGE view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX LGE']
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([SAX_LGE_Category])
            case.other_categories['SAX LGE'] = case.categories
        else:
            if 'SAX LGE' in case.other_categories.keys(): case.categories = case.other_categories['SAX LGE']
            else: case.attach_categories([SAX_LGE_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([SAXLGE_LVV,       SAXLGE_LVMYOV, 
                                      SAXLGE_LVMYOMASS, SAXLGE_SCARVOL,
                                      SAXLGE_SCARMASS,  SAXLGE_SCARF,
                                      SAXLGE_EXCLVOL,   SAXLGE_EXCLMASS,
                                      SAXLGE_NOREFLOWVOL])
        # set new type
        case.type = 'SAX LGE'
        if debug: print('Customization in SAX LGE view took: ', time()-st)
        return case

