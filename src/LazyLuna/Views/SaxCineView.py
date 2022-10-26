from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class SAX_CINE_View(View):
    def __init__(self):
        self.load_categories()
        self.contour2categorytype = {None      : self.all,    'lv_endo' : self.lvcats,  'lv_epi'  : self.myocats,
                                     'lv_pamu' : self.lvcats, 'lv_myo'  : self.myocats, 'rv_endo' : self.rvcats,
                                     'rv_epi'  : self.rvcats, 'rv_pamu' : self.rvcats,  'rv_myo'  : self.rvcats}
        self.contour_names = ['lv_endo', 'lv_epi', 'lv_pamu', 'lv_myo',
                              'rv_endo', 'rv_epi', 'rv_pamu', 'rv_myo']
        
        import LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab                      as tab1
        import LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_tab             as tab2
        import LazyLuna.Guis.Addable_Tabs.CCs_Qualitative_Correlationplot_Tab as tab3
        import LazyLuna.Guis.Addable_Tabs.CC_Overview_Tab                     as tab4
        
        self.case_tabs  = {'Metrics and Figure':          tab1.CC_Metrics_Tab, 
                           'Clinical Results and Images': tab4.CC_CRs_Images_Tab}
        self.stats_tabs = {'Clinical Results':            tab2.CCs_ClinicalResults_Tab, 
                           'Qualitative Metrics Correlation Plot': tab3.CCs_Qualitative_Correlationplot_Tab}
        
    def load_categories(self):
        self.lvcats, self.rvcats  = [SAX_LV_ES_Category, SAX_LV_ED_Category], [SAX_RV_ES_Category, SAX_RV_ED_Category]
        self.myocats              = [SAX_LV_ED_Category]
        self.all = [SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category]

    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CINE']
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        case.other_categories['SAX CINE'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'SAX CINE'
        case.available_types.add('SAX CINE')
        if debug: print('Customization in SAX CINE view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CINE']
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
            case.other_categories['SAX CINE'] = case.categories
        else:
            if 'SAX CINE' in case.other_categories.keys(): case.categories = case.other_categories['SAX CINE']
            else: case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([LVSAX_ESV, LVSAX_EDV, RVSAX_ESV, RVSAX_EDV,
                                      LVSAX_SV, LVSAX_EF, RVSAX_SV, RVSAX_EF,
                                      LVSAX_MYO, RVSAX_MYO,
                                      LVSAX_ESPHASE, RVSAX_ESPHASE, LVSAX_EDPHASE, RVSAX_EDPHASE,
                                      NR_SLICES])
        # set new type
        case.type = 'SAX CINE'
        if debug: print('Customization in SAX CINE view took: ', time()-st)
        return case
    
    def store_information(self, ccs, path):
        try:
            cr_table = CCs_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print(traceback.print_exc())
        try:
            cr_overview_figure = SAX_BlandAltman()
            cr_overview_figure.visualize(ccs)
            cr_overview_figure.store(path)
        except Exception as e:
            print(traceback.print_exc())
        try:
            ci_figure = SAXCINE_Confidence_Intervals_Tolerance_Ranges()
            ci_figure.visualize(ccs, True)
            ci_figure.store(path)
        except Exception as e:
            print(traceback.print_exc())
        try:
            metrics_table = SAX_CINE_CCs_Metrics_Table()
            metrics_table.calculate(self, ccs)
            metrics_table.store(os.path.join(path, 'metrics_phase_slice_table.csv'))
        except Exception as e:
            print(traceback.print_exc())
        try:
            failed_segmentation_folder_path = os.path.join(path, 'Failed_Segmentations')
            if not os.path.exists(failed_segmentation_folder_path): os.mkdir(failed_segmentation_folder_path)
            failed_annotation_comparison = Failed_Annotation_Comparison_Yielder()
            failed_annotation_comparison.set_values(self, ccs)
            failed_annotation_comparison.store(failed_segmentation_folder_path)
        except Exception as e:
            print(traceback.print_exc())
        try:
            table = SAX_Cine_CCs_pretty_averageCRs_averageMetrics_Table()
            table.calculate(ccs, self)
            table.present_metrics()
            table.store(os.path.join(path, 'metrics_table_by_contour_position.csv'))
            table.present_crs()
            table.store(os.path.join(path, 'crvs_and_metrics.csv'))
        except Exception as e:
            print(traceback.print_exc())
