########
# View #
########
#
# Views take case of customizing cases, images, outputs and tabs to specific use cases
#
#

from LazyLuna.Mini_LL    import *
from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class View:
    def __init__(self):
        pass

    def store_information(self, ccs, path):
        pass


class SAX_CINE_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
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
        # attach annotation type
        case.attach_annotation_type(Annotation)
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
        print('starting customize: ', case.case_name)
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CINE']
        # attach annotation type
        case.attach_annotation_type(Annotation)
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
        print('ending customize: ', case.case_name)
        return case
    
    def store_information(self, ccs, path):
        try:
            cr_table = CC_ClinicalResultsTable()
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
            metrics_table = CCs_MetricsTable()
            metrics_table.calculate(ccs, self)
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




class SAX_CS_View(SAX_CINE_View):
    def __init__(self):
        super().__init__()

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CS']
        # attach annotation type
        case.attach_annotation_type(Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        case.other_categories['SAX CS'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'SAX CS'
        case.available_types.add('SAX CS')
        if debug: print('Customization in SAX CS view took: ', time()-st)
        return case
        
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CS']
        # attach annotation type
        case.attach_annotation_type(Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if 'SAX CS' in case.other_categories.keys(): case.categories = case.other_categories['SAX CS']
        else: case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([LVSAX_ESV, LVSAX_EDV, RVSAX_ESV, RVSAX_EDV,
                                      LVSAX_SV, LVSAX_EF, RVSAX_SV, RVSAX_EF,
                                      LVSAX_MYO, RVSAX_MYO,
                                      LVSAX_ESPHASE, RVSAX_ESPHASE, LVSAX_EDPHASE, RVSAX_EDPHASE,
                                      NR_SLICES])
        # set new type
        case.type = 'SAX CS'
        if debug: print('Customization in SAX CS view took: ', time()-st)
        return case

    

class LAX_CINE_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
        self.load_categories()
        """
        self.contour_names        = ['lv_lax_endo', 'lv_lax_myo', 'rv_lax_endo', 'la', 'ra']
        self.contour2categorytype = {None : self.all,
                         'lv_lax_endo': self.lv_cats,  'lv_lax_epi' : self.myo_cats,
                         'lv_lax_myo' : self.myo_cats, 'rv_lax_endo': self.rv_cats,
                         'la'         : self.la_cats,  'ra'         : self.ra_cats}
        """
        self.contour_names        = ['la', 'ra']
        self.contour2categorytype = {None : self.all, 
                                     'la': self.la_cats, 'ra': self.ra_cats}
        
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
        case.imgs_sop2filepath = {**case.all_imgs_sop2filepath['LAX 2CV'],
                                  **case.all_imgs_sop2filepath['LAX 4CV']}
        # attach annotation type
        case.attach_annotation_type(Annotation)
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
        case.imgs_sop2filepath = {**case.all_imgs_sop2filepath['LAX 2CV'], 
                                  **case.all_imgs_sop2filepath['LAX 4CV']}
        # attach annotation type
        case.attach_annotation_type(Annotation)
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
            metrics_table.calculate(ccs, self)
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

            
class SAX_T1_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
        self.load_categories()
        self.contour_names = ['lv_endo', 'lv_myo']
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
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX T1']
        # attach annotation type
        case.attach_annotation_type(Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_T1_Category])
        cat = case.categories[0]
        case.other_categories['SAX T1'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'SAX T1'
        case.available_types.add('SAX T1')
        if debug: print('Customization in SAX T1 view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug:
            print('starting customize t1: ', case.case_name)
            st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX T1']
        # attach annotation type
        case.attach_annotation_type(Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([SAX_T1_Category])
            case.other_categories['SAX T1'] = case.categories
        else:
            if 'SAX T1' in case.other_categories.keys(): case.categories = case.other_categories['SAX T1']
            else: case.attach_categories([SAX_T1_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([SAXMap_GLOBALT1, NR_SLICES])
        # set new type
        case.type = 'SAX T1'
        if debug: 
            print('Customization in SAX T1 view took: ', time()-st)
            print('ending customize: ', case.case_name)
        return case
    
    def store_information(self, ccs, path):
        try:
            cr_table = CC_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print('CR Table store exeption: ', traceback.print_exc())
        try:
            metrics_table = T1_CCs_MetricsTable()
            metrics_table.calculate(ccs, self)
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
        
    

class SAX_T2_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
        self.load_categories()
        self.contour_names = ['lv_endo', 'lv_myo']
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
        # attach annotation type
        case.attach_annotation_type(Annotation)
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
        # attach annotation type
        case.attach_annotation_type(Annotation)
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
            cr_table = CC_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print('CR Table store exeption: ', traceback.print_exc())
        try:
            metrics_table = T2_CCs_MetricsTable()
            metrics_table.calculate(ccs, self)
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
        
    

class SAX_LGE_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
        self.load_categories()
        # contour names with scars
        self.contour_names = ['lv_endo', 'lv_myo', 'scar', 'noreflow']
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
        # attach annotation type
        #case.attach_annotation_type(SAX_LGE_Annotation)
        case.attach_annotation_type(Annotation)
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
        # attach annotation type
        case.attach_annotation_type(Annotation)
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

