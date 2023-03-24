from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import *

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback

import csv
import PIL

import time


class SAX_CINE_View(View):
    def __init__(self):
        self.name = 'SAX CINE'
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
                                      LVSAX_MYO, RVSAX_MYO, LVSAX_ESPAPMUM, LVSAX_EDPAPMUM,
                                      LVSAX_ESPHASE, RVSAX_ESPHASE, LVSAX_EDPHASE, RVSAX_EDPHASE,
                                      NR_SLICES])
        # set new type
        case.type = 'SAX CINE'
        if debug: print('Customization in SAX CINE view took: ', time()-st)
        return case
    
    def store_information(self, ccs, path, icon_path, storage_version=0):
        st = time.time()
        if storage_version >= 0:
            try:
                cr_table = CC_ClinicalResultsAveragesTable()
                cr_table.calculate(ccs)
                crtol_p = cr_table.store(os.path.join(path, 'clinical_results_overview.csv'))
            except Exception as e: print(traceback.print_exc())
            try:
                cr_table = CCs_ClinicalResultsTable()
                cr_table.calculate(ccs)
                cr_table.store(os.path.join(path, 'clinical_results.csv'))
            except Exception as e: print(traceback.print_exc())
            try:
                cr_overview_figure = SAX_BlandAltman()
                cr_overview_figure.visualize(ccs)
                cr_p = cr_overview_figure.store(path)
            except Exception as e: print(traceback.print_exc())
            try:
                ci_figure = SAXCINE_Confidence_Intervals_Tolerance_Ranges()
                ci_figure.visualize(ccs, True)
                ci_p = ci_figure.store(path)
            except Exception as e: print(traceback.print_exc())
            try:
                metrics_table = SAX_CINE_CCs_Metrics_Table()
                metrics_table.calculate(self, ccs)
                metrics_table.store(os.path.join(path, 'metrics_phase_slice_table.csv'))
            except Exception as e: print(traceback.print_exc())
            try:
                failed_segmentation_folder_path = os.path.join(path, 'Failed_Segmentations')
                if not os.path.exists(failed_segmentation_folder_path): os.mkdir(failed_segmentation_folder_path)
                """
                failed_annotation_comparison = Failed_Annotation_Comparison_Yielder()
                failed_annotation_comparison.set_values(self, ccs)
                failed_annotation_comparison.store(failed_segmentation_folder_path)
                """
            except Exception as e: print(traceback.print_exc())
        if storage_version >= 1:
            try:
                table = SAX_Cine_CCs_pretty_averageCRs_averageMetrics_Table()
                table.calculate(ccs, self)
                table.present_metrics()
                table.store(os.path.join(path, 'metrics_table_by_contour_position.csv'))
                table.present_crs()
                table.store(os.path.join(path, 'crvs_and_metrics.csv'))
            except Exception as e: print(traceback.print_exc())
            
        print('Storing took: ', time.time()-st)
        st = time.time()
            
        pdf = PDF(orientation='P', unit='mm', format='A4')
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                # CRs TABLE
                data = [l[1:] for l in csv.reader(open(os.path.join(path, 'clinical_results_overview.csv')), delimiter=';')]
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        try:    data[i][j] = "{:10.2f}".format(float(data[i][j].replace(',','.')))
                        except: data[i][j] = data[i][j]
                pdf.set_title('Clinical Parameter Means and Tolerance Ranges')
                pdf.set_table(data[0:], x=15, y=30, col_widths=[40.0]+[30 for i in range(len(data[0])-2)]+[40.0])
                pdf.set_text("Table. 1 This table shows the clinical parameter names in the first column. The other columns show statistics concerning the parameters. The first and second readers' means (stds) are shown in the second and third column, respectively. The mean and std of the differences between both readers is presented in the fourth column. The mean difference of both readers ± 95% confidence intervals are shown in parentheses with ±tolerance ranges thereafter. This provides information on whether the 95% estimate of the mean difference between both readers is within an acceptable limit.", 10, 192)
                pdf.set_text('Tolerance range paper: Zange L, Muehlberg F, Blaszczyk E, Schwenke S, Traber J, Funk S, et al. Quantification in cardiovascular magnetic resonance: agreement of software from three different vendors on assessment of left ventricular function, 2D flow and parametric mapping. J Cardiovasc Magn Reson. 2019 Dec;21(1):12.', 10, 215)
            except: print(traceback.print_exc())
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title('Clinical Results Differences')
                pdf.set_chart(cr_p, 20, 35, w=695/4, h=841/4)
                pdf.set_text('Fig. 1 Clinical Parameter Bland-Altmans: Bland-Altman plots show clinical parameter averages and differences as points for all cases. Point size represents difference, the solid line marks the mean difference between readers, the dashed lines mark the mean differences ±1.96 standard deviations. The last plot offers two Dice boxplots per contour type, one for all images, another restricted to images segmented by both readers. Legend: GUI: Graphical user interface, RV: Right ventricle, LV: Left ventricle, ESV: End-systolic volume, EDV: End-diastolic volume, EF: Ejection fraction, LVM: Left ventricular mass, Dice: Dice similarity coefficient', 10, 242)
            except: print(traceback.print_exc())
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title('Confidence Intervals')
                pdf.set_chart(ci_p, 20, 35, w=695/4, h=695/4)
                pdf.set_text('Fig. 2 Tolerance Ranges and Confidence Intervals: Each subfigure references a clinical parameter. Tolerance intervals are shown as gray bars and represent ±1.96 standard deviation of an expert intrareader deviation as derived in another publication (see below). The 95% confidence intervals of the mean value is represented as an error bar in red. Individual clinical parameter differences per case are plotted in blue. Legend: LV: Left ventricle, RV: Right ventricle, ESV: end-systolic volume, EDV: end-diastolic volume, EF: ejection fraction, LVM: Left ventricular myocardium.', 10, 210)
                pdf.set_text('Tolerance range paper: Zange L, Muehlberg F, Blaszczyk E, Schwenke S, Traber J, Funk S, et al. Quantification in cardiovascular magnetic resonance: agreement of software from three different vendors on assessment of left ventricular function, 2D flow and parametric mapping. J Cardiovasc Magn Reson. 2019 Dec;21(1):12.', 10, 235)
            except: print(traceback.print_exc())
        
        if storage_version>=1:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                # METRICS TABLE
                data = [l[2:] for l in csv.reader(open(os.path.join(path, 'metrics_table_by_contour_position.csv')), delimiter=';')]
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        try: data[i][j] = "{:10.2f}".format(float(data[i][j].replace(',','.')))
                        except: data[i][j] = data[i][j]
                # header
                pdf.set_table(data[0:1], x=20, y=30, col_widths=[47.0]+[35 for i in range(len(data[0])-1)])
                # basal
                pdf.set_title('Metrics by Cardiac Location and Contour Type')
                pdf.set_text('Basal Slices', 25, 50, size=12)
                pdf.set_table(data[1:5], x=20, y=50, col_widths=[47.0]+[35 for i in range(len(data[0])-1)])
                # midv
                pdf.set_text('Midventricular Slices', 25, 95, size=12)
                pdf.set_table(data[5:9], x=20, y=95, col_widths=[47.0]+[35 for i in range(len(data[0])-1)])
                # apical
                pdf.set_text('Apical Slices', 25, 140, size=12)
                pdf.set_table(data[9:], x=20, y=140, col_widths=[47.0]+[35 for i in range(len(data[0])-1)])
                pdf.set_text('Table. 1 Clinical Parameters and Metrics Table: The columnms are metric name, left ventricular endocardial contour, left ventricular myocardial contour, right ventricular endocardial contour. The table is divided into basal midventricular and apical slices. Basal slices are the most upper slice, apical the lowest slice (as defined by the first reader). Legend: LV left ventricular, RV: Right ventricular, Dice: Dice similarity coefficient, HD: Hausdorff distance, Abs. ml diff.: Absolute millilitre difference', 10, 185)
            except: print(traceback.print_exc())
        
        
        if storage_version>=1:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                data = [l[1:] for l in csv.reader(open(os.path.join(path, 'crvs_and_metrics.csv')), delimiter=';')]
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        try: data[i][j] = "{:10.2f}".format(float(data[i][j].replace(',','.')))
                        except: data[i][j] = data[i][j]
                pdf.set_title('Clinical Parameters and Metrics Table')
                pdf.set_table(data[0:], x=40, y=30, col_widths=[65.0]+[25 for i in range(len(data[0])-1)])
                pdf.set_text('Table. 2 Clinical Parameters and Metrics Table: The columns are Name (either clinical parameter or metric), Mean and Standard deviation (for difference if clinical parameter, or mean value for metric). Legend: LV: Left ventricle, RV: Right ventricle, EF: Ejection fraction, EDV: end-diastolic volume, ESV: end-systolic volume, Dice: Dice similarity coefficient, HD: Hausdorff distance', 10, 223)
            except: print(traceback.print_exc())
        
        print('Time for stats in pdf took: ', time.time()-st)
        
        st = time.time()
        # ADD the QUALITATIVE FIGURES
        try:
            overviewtab = findCCsOverviewTab()
            view_name = type(self).__name__.replace('_View','').replace('_',' ')
            print(overviewtab.qualitative_figures)
            if len(overviewtab.qualitative_figures[view_name])!=0:
                
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title('Qualitative Figures added during Manual Inspection')
                pdf.set_text('The following PDF pages reference figures, which were manually selected by the investigor and added to this report manually. Every figure has a title and comments that the investigator typed for elaboration.', 10, 50, size=12)
                
                for addable in overviewtab.qualitative_figures[view_name]:
                    pdf.add_page()
                    pdf.prepare_pretty_format()
                    img = PIL.Image.open(addable[1])
                    scale = img.height / img.width
                    pdf.set_text('Title:    ' + addable[0], 10, 20, size=12)
                    pdf.set_chart(addable[1], 20, 35, w=695/4, h=695/4*scale)
                    pdf.set_text(addable[2], 10, 40 + 695/4*scale)
        except Exception as e: print(traceback.print_exc())
        
        print('PDF TOOK: ', time.time()-st)
        
        pdf.set_author('Luna Lovegood')
        pdf.output(os.path.join(path, view_name+'_summary_PDF.pdf'))
        
            
