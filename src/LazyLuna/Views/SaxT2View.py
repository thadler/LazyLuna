from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class SAX_T2_View(View):
    def __init__(self):
        self.load_categories()
        self.contour_names = ['lv_myo', 'lv_endo']
        self.point_names   = ['sacardialRefPoint']
        self.contour2categorytype = {cname:self.all for cname in self.contour_names}
        
        # register tabs here:
        import LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab          as tab1
        import LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_tab as tab2
        import LazyLuna.Guis.Addable_Tabs.CC_Angle_Segments_Tab   as tab3
        import LazyLuna.Guis.Addable_Tabs.CC_Overview_Tab         as tab4
        
        self.case_tabs  = {'Metrics and Figure': tab1.CC_Metrics_Tab, 'Clinical Results and Images': tab4.CC_CRs_Images_Tab, 'T2 Angle Comparison': tab3.CC_Angle_Segments_Tab}
        self.stats_tabs = {'Clinical Results'  : tab2.CCs_ClinicalResults_Tab}
        
    def load_categories(self):
        self.all = [SAX_T2_Category]

    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX T2']
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_T2_Category])
        cat = case.categories[0]
        case.other_categories['SAX T2'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'SAX T2'
        case.available_types.add('SAX T2')
        if debug: print('Customization in SAX T2 view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX T2']
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([SAX_T2_Category])
            case.other_categories['SAX T2'] = case.categories
        else:
            if 'SAX T2' in case.other_categories.keys(): case.categories = case.other_categories['SAX T2']
            else: case.attach_categories([SAX_T2_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([SAXMap_GLOBALT2, NR_SLICES])
        # set new type
        case.type = 'SAX T2'
        if debug: print('Customization in SAX T2 view took: ', time()-st)
        return case

    def store_information(self, ccs, path):
        try:
            cr_table = CCs_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print('CR Table store exeption: ', traceback.print_exc())
        try:
            metrics_table = T2_CCs_MetricsTable()
            metrics_table.calculate(self, ccs)
            metrics_table.store(os.path.join(path, 'metrics_phase_slice_table.csv'))
        except Exception as e:
            print('Metrics Table store exeption: ', traceback.print_exc())
        try:
            failed_segmentation_folder_path = os.path.join(path, 'Failed_Segmentations')
            if not os.path.exists(failed_segmentation_folder_path): os.mkdir(failed_segmentation_folder_path)
            failed_annotation_comparison = Failed_Annotation_Comparison_Yielder()
            failed_annotation_comparison.set_values(self, ccs)
            failed_annotation_comparison.store(failed_segmentation_folder_path)
        except Exception as e:
            print(traceback.print_exc())
        