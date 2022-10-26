from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class SAX_T1_PRE_View(View):
    def __init__(self):
        self.ll_tag = 'SAX T1 PRE'
        self.load_categories()
        self.contour_names = ['lv_myo', 'lv_endo']
        self.point_names   = ['sacardialRefPoint']
        self.contour2categorytype = {cname:self.all for cname in self.contour_names}
        
        # register tabs here:
        import LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab          as tab1
        import LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_tab as tab2
        import LazyLuna.Guis.Addable_Tabs.CC_Angle_Segments_Tab   as tab3
        import LazyLuna.Guis.Addable_Tabs.CC_Overview_Tab         as tab4
        import LazyLuna.Guis.Addable_Tabs.CC_AHA_Tab              as tab5
        import LazyLuna.Guis.Addable_Tabs.CC_AHA_Diff_Tab         as tab6
        import LazyLuna.Guis.Addable_Tabs.CCs_AHA_Tab             as tab7
        import LazyLuna.Guis.Addable_Tabs.CCs_AHA_Diff_Tab        as tab8
        
        self.case_tabs  = {'Metrics and Figure': tab1.CC_Metrics_Tab, 
                           'Clinical Results and Images': tab4.CC_CRs_Images_Tab, 
                           'T1 Angle Comparison': tab3.CC_Angle_Segments_Tab, 
                           'AHA Model' : tab5.CC_AHA_Tab, 
                           'AHA Diff Model' : tab6.CC_AHA_Diff_Tab
                          }
        self.stats_tabs = {'Clinical Results' : tab2.CCs_ClinicalResults_Tab,
                           'Averaged AHA Tab' : tab7.CCs_AHA_Tab,
                           'Averaged AHA Diff Tab' : tab8.CCs_AHA_Diff_Tab}
        
    def load_categories(self):
        self.all = [SAX_T1_Category]

    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath[self.ll_tag]
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_T1_Category])
        cat = case.categories[0]
        case.other_categories[self.ll_tag] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = self.ll_tag
        case.available_types.add(self.ll_tag)
        if debug: print('Customization in SAX T1 PRE view took: ', time()-st)
        return case
    
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
        case.attach_clinical_results([SAXMap_GLOBALT1, NR_SLICES])
        # set new type
        case.type = self.ll_tag
        if debug: 
            print('Customization in SAX T1 PRE view took: ', time()-st)
            print('ending customize: ', case.case_name)
        return case
    
    def store_information(self, ccs, path):
        try:
            cr_table = CCs_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print('CR Table store exeption: ', traceback.print_exc())
        try:
            metrics_table = T1_CCs_MetricsTable()
            #metrics_table.calculate(ccs, self)
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
            