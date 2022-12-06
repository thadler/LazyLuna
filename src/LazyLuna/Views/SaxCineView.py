from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback

from fpdf import FPDF
import csv


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
    
    def store_information(self, ccs, path, icon_path):
        pdf = PDF(orientation='P', unit='mm', format='A4')

        try:
            cr_table = CCs_ClinicalResultsTable()
            cr_table.calculate(ccs)
            cr_table.store(os.path.join(path, 'clinical_results.csv'))
        except Exception as e:
            print(traceback.print_exc())
        try:
            cr_overview_figure = SAX_BlandAltman()
            cr_overview_figure.visualize(ccs)
            p = cr_overview_figure.store(path)
            
            pdf.add_page()
            pdf.prepare_pretty_format(icon_path)
            pdf.set_title('Clinical Results Differences')
            pdf.set_chart(p, 20, 35, w=695/4, h=841/4)
            pdf.set_text('Fig. 1 Clinical Parameter Bland-Altmans: Bland-Altman plots show clinical parameter averages and differences as points for all cases. Point size represents difference, the solid line marks the mean difference between readers, the dashed lines mark the mean differences ±1.96 standard deviations. The last plot offers two Dice boxplots per contour type, one for all images, another restricted to images segmented by both readers. Legend: GUI: Graphical user interface, RV: Right ventricle, LV: Left ventricle, ESV: End-systolic volume, EDV: End-diastolic volume, EF: Ejection fraction, LVM: Left ventricular mass, Dice: Dice similarity coefficient', 10, 245)

        except Exception as e:
            print(traceback.print_exc())
        try:
            ci_figure = SAXCINE_Confidence_Intervals_Tolerance_Ranges()
            ci_figure.visualize(ccs, True)
            p = ci_figure.store(path)
            
            pdf.add_page()
            pdf.prepare_pretty_format(icon_path)
            pdf.set_title('Confidence Intervals')
            pdf.set_chart(p, 20, 35, w=695/4, h=695/4)
            pdf.set_text('Fig. 2 Confidence Intervals', 10, 205)
            
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
            pdf.set_text('Table. 1 Clinical Parameters and Metrics Table', 10, 205)
            
            # CRS AND METRICS TABLE
            pdf.add_page()
            pdf.prepare_pretty_format(icon_path)
            data = [l[1:] for l in csv.reader(open(os.path.join(path, 'crvs_and_metrics.csv')), delimiter=';')]
            for i in range(len(data)):
                for j in range(len(data[i])):
                    try: data[i][j] = "{:10.2f}".format(float(data[i][j].replace(',','.')))
                    except: data[i][j] = data[i][j]
            pdf.set_title('Clinical Parameters and Metrics Table')
            pdf.set_table(data[0:], x=40, y=50, col_widths=[65.0]+[25 for i in range(len(data[0])-1)])
            
        except Exception as e:
            print(traceback.print_exc())
        
        pdf.set_author('Thomas Hadler')
        pdf.output(os.path.join(path, 'summary_PDF.pdf'))

            
            


class PDF(FPDF):
    def prepare_pretty_format(self, icon_path=None):
        # Outside Rectangle
        self.set_fill_color(132.0, 132.0, 132.0) # color for outer rectangle
        self.rect(5.0, 5.0, 200.0, 287.0, 'DF')
        self.set_fill_color(255, 255, 255)       # color for inner rectangle
        self.rect(8.0, 8.0, 194.0, 281.0, 'FD')
        # Hogwarts Image
        try: 
            self.set_xy(170.0, 9.0)
            self.image(os.path.join(icon_path, 'HogwartsLineArt.png'),  link='', type='', w=2520/80, h=1920/80)
        except Exception as e: print('no icon path: ', e)
        try:
            self.set_xy(195.0, 7.5)
            self.image(os.path.join(icon_path, 'SlothLineArt.png'),  link='', type='', w=520/80, h=520/80)
        except Exception as e: print('no icon path: ', e)
        self.set_xy(173.5, 28.0)
        self.set_font('Times', 'B', 10)
        self.set_text_color(10, 10, 10)
        self.cell(w=25.0, h=6.0, align='C', txt='Lazy        Luna', border=0)
        
    def set_title(self, text):
        self.set_xy(0.0,0.0)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(50, 50, 50)
        self.cell(w=210.0, h=40.0, align='C', txt=text, border=0)
        
    def set_text(self, text, x=10.0, y=80.0, font='Arial', size=8):
        self.set_xy(x, y)
        self.set_text_color(70.0, 70.0, 70.0)
        self.set_font(font, '', size)
        self.multi_cell(0, 5, text)
        
    def set_chart(self, plot_path, x=30.0, y=30, w=695/4, h=695/4):
        self.set_xy(x, y)
        self.image(plot_path, link='', type='', w=w, h=h)
        
        
    def set_table(self, data, spacing=1, fontsize=8, x=30.0, y=30, w=695/4, col_widths=None):
        self.set_xy(x, y)
        self.set_font('Arial', size=8)
        if col_widths is None: col_widths = [w/4.5 for i in range(len(data[0]))]
        else: pass
        row_height = fontsize
        for row in data:
            self.ln(row_height*spacing)
            curr_x = x
            for j, item in enumerate(row):
                self.set_x(curr_x)
                self.cell(col_widths[j], row_height*spacing, txt=item, border=1)
                curr_x += col_widths[j]
