from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class LAX_CINE_View(View):
    def __init__(self):
        self.load_categories()
        """
        self.contour_names        = ['lv_lax_endo', 'lv_lax_myo', 'rv_lax_endo', 'la', 'ra']
        self.contour2categorytype = {None : self.all,
                         'lv_lax_endo': self.lv_cats,  'lv_lax_epi' : self.myo_cats,
                         'lv_lax_myo' : self.myo_cats, 'rv_lax_endo': self.rv_cats,
                         'la'         : self.la_cats,  'ra'         : self.ra_cats}
        """
        self.contour_names        = ['la', 'ra']
        self.contour2categorytype = {None : self.all, 'la': self.la_cats, 'ra': self.ra_cats}
        
        # register tabs here:
        """
        from LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab                        import CC_Metrics_Tab
        from LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_Tab               import CCs_ClinicalResults_Tab
        from LazyLuna.Guis.Addable_Tabs.CCs_Qualitative_Correlationplot_Tab   import CCs_Qualitative_Correlationplot_Tab
        self.case_tabs  = {'Metrics and Figure': CC_Metrics_Tab}
        self.stats_tabs = {'Clinical Results'  : CCs_ClinicalResults_Tab}
        """
        import LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab          as tab1
        import LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_tab as tab2
        import LazyLuna.Guis.Addable_Tabs.CC_Overview_Tab         as tab4
        
        self.case_tabs  = {'Metrics and Figure': tab1.CC_Metrics_Tab, 'Clinical Results and Images': tab4.CC_CRs_Images_Tab}
        self.stats_tabs = {'Clinical Results'  : tab2.CCs_ClinicalResults_Tab}
        
    def load_categories(self):
        """
        self.all = [LAX_4CV_LVES_Category, LAX_4CV_LVED_Category, LAX_4CV_RVES_Category, 
                    LAX_4CV_RVED_Category, LAX_4CV_LAES_Category, LAX_4CV_LAED_Category, 
                    LAX_4CV_RAES_Category, LAX_4CV_RAED_Category, LAX_2CV_LVES_Category, 
                    LAX_2CV_LVED_Category, LAX_2CV_LAES_Category, LAX_2CV_LAED_Category]
        """
        self.lv_cats  = []#[LAX_4CV_LVES_Category, LAX_4CV_LVED_Category, LAX_2CV_LVES_Category, LAX_2CV_LVED_Category]
        self.myo_cats = []#[LAX_4CV_LVED_Category, LAX_2CV_LVED_Category]
        self.rv_cats  = []#[LAX_4CV_RVES_Category, LAX_4CV_RVED_Category]
        self.la_cats  = [LAX_2CV_LAES_Category, LAX_2CV_LAED_Category,
                         LAX_4CV_LAES_Category, LAX_4CV_LAED_Category]
        self.ra_cats  = [LAX_4CV_RAES_Category, LAX_4CV_RAED_Category]
        self.all      = self.lv_cats + self.myo_cats + self.rv_cats + self.la_cats + self.ra_cats
        
    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = {**case.all_imgs_sop2filepath['LAX CINE 2CV'],
                                  **case.all_imgs_sop2filepath['LAX CINE 4CV']}
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        """
        case.attach_categories([LAX_4CV_LVES_Category, LAX_4CV_LVED_Category,
                                LAX_4CV_RVES_Category, LAX_4CV_RVED_Category,
                                LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                LAX_2CV_LVES_Category, LAX_2CV_LVED_Category,
                                LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
        """
        case.attach_categories([LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
        case.other_categories['LAX CINE'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'LAX CINE'
        case.available_types.add('LAX CINE')
        if debug: print('Customization in LAX CINE view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = {**case.all_imgs_sop2filepath['LAX CINE 2CV'], 
                                  **case.all_imgs_sop2filepath['LAX CINE 4CV']}
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            """
            case.attach_categories([LAX_4CV_LVES_Category, LAX_4CV_LVED_Category,
                                    LAX_4CV_RVES_Category, LAX_4CV_RVED_Category,
                                    LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                    LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                    LAX_2CV_LVES_Category, LAX_2CV_LVED_Category,
                                    LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
            """
            case.attach_categories([LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                    LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                    LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
            case.other_categories['LAX CINE'] = case.categories
        else:
            if 'LAX CINE' in case.other_categories.keys(): case.categories = case.other_categories['LAX CINE']
            else: 
                """
                case.attach_categories(
                [LAX_4CV_LVES_Category, LAX_4CV_LVED_Category,
                 LAX_4CV_RVES_Category, LAX_4CV_RVED_Category,
                 LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                 LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                 LAX_2CV_LVES_Category, LAX_2CV_LVED_Category,
                 LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
                 """
                case.attach_categories(
                [LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                 LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                 LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        """
        case.attach_clinical_results([LAX_4CV_LVESV,      LAX_4CV_LVEDV,
                                      LAX_4CV_LVSV,       LAX_4CV_LVEF,
                                      LAX_2CV_LVESV,      LAX_2CV_LVEDV,
                                      LAX_2CV_LVSV,       LAX_2CV_LVEF,
                                      LAX_2CV_LVM,        LAX_4CV_LVM,
                                      LAX_BIPLANE_LVESV,  LAX_BIPLANE_LVEDV,
                                      LAX_BIPLANE_LVSV,   LAX_BIPLANE_LVEF,
                                      LAX_4CV_RAESAREA,   LAX_4CV_RAEDAREA,
                                      LAX_4CV_RAESV,      LAX_4CV_RAEDV,
                                      LAX_4CV_LAESAREA,   LAX_4CV_LAEDAREA,
                                      LAX_4CV_LAESV,      LAX_4CV_LAEDV,
                                      LAX_2CV_LAESAREA,   LAX_2CV_LAEDAREA,
                                      LAX_2CV_LAESV,      LAX_2CV_LAEDV,
                                      LAX_BIPLANAR_LAESV, LAX_BIPLANAR_LAEDV,
                                 LAX_2CV_ESAtrialFatArea, LAX_2CV_EDAtrialFatArea, 
                                 LAX_4CV_ESAtrialFatArea, LAX_4CV_EDAtrialFatArea,
                       LAX_2CV_ESEpicardialFatArea,  LAX_2CV_EDEpicardialFatArea,
                       LAX_4CV_ESEpicardialFatArea,  LAX_4CV_EDEpicardialFatArea,
                       LAX_2CV_ESPericardialFatArea, LAX_2CV_EDPericardialFatArea,
                       LAX_4CV_ESPericardialFatArea, LAX_4CV_EDPericardialFatArea])
        """
        case.attach_clinical_results([LAX_4CV_RAESAREA,   LAX_4CV_RAEDAREA,
                                      LAX_4CV_RAESV,      LAX_4CV_RAEDV,
                                      LAX_4CV_LAESAREA,   LAX_4CV_LAEDAREA,
                                      LAX_4CV_LAESV,      LAX_4CV_LAEDV,
                                      LAX_2CV_LAESAREA,   LAX_2CV_LAEDAREA,
                                      LAX_2CV_LAESV,      LAX_2CV_LAEDV,
                                      LAX_BIPLANAR_LAESV, LAX_BIPLANAR_LAEDV,
                                      LAX_4CV_LAESPHASE,  LAX_4CV_LAEDPHASE,
                                      LAX_2CV_LAESPHASE,  LAX_2CV_LAEDPHASE,
                                      LAX_4CV_RAESPHASE,  LAX_4CV_RAEDPHASE])
        # set new type
        case.type = 'LAX CINE'
        if debug: print('Customization in LAX CINE view took: ', time()-st)
        return case
    
    def store_information(self, ccs, path):
        try:
            cr_table = CC_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print(traceback.print_exc())
        try:
            cr_overview_figure = LAX_BlandAltman()
            cr_overview_figure.visualize(self, ccs)
            cr_overview_figure.store(path)
        except Exception as e:
            print(traceback.print_exc())
        try:
            cr_overview_figure = LAX_Volumes_BlandAltman()
            cr_overview_figure.visualize(self, ccs)
            cr_overview_figure.store(path)
        except Exception as e:
            print(traceback.print_exc())
        try:
            metrics_table = LAX_CCs_MetricsTable()
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
            conf_visualization = LAXCINE_Confidence_Intervals_Tolerance_Ranges()
            conf_visualization.visualize(ccs)
            conf_visualization.store(path)
        except Exception as e:
            print(traceback.print_exc())

