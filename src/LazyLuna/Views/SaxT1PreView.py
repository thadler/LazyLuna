from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.View import *

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import csv
import PIL

import traceback


class SAX_T1_PRE_View(View):
    def __init__(self):
        self.ll_tag = 'SAX T1 PRE'
        self.load_categories()
        self.contour_names = ['lv_myo', 'lv_endo']
        self.point_names   = ['sacardialRefPoint']
        self.contour2categorytype = {cname:self.all for cname in self.contour_names}
        
        # register tabs here:
        import LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab               as tab1
        import LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_tab      as tab2
        import LazyLuna.Guis.Addable_Tabs.CC_Angle_Segments_Tab        as tab3
        import LazyLuna.Guis.Addable_Tabs.CC_Overview_Tab              as tab4
        import LazyLuna.Guis.Addable_Tabs.CC_AHA_Tab                   as tab5
        import LazyLuna.Guis.Addable_Tabs.CC_AHA_Diff_Tab              as tab6
        import LazyLuna.Guis.Addable_Tabs.CCs_AHA_Tab                  as tab7
        import LazyLuna.Guis.Addable_Tabs.CCs_AHA_Diff_Tab             as tab8
        import LazyLuna.Guis.Addable_Tabs.CCs_Mapping_Slice_Analysis   as tab9
        
        self.case_tabs  = {'Metrics and Figure': tab1.CC_Metrics_Tab, 
                           'Clinical Results and Images': tab4.CC_CRs_Images_Tab, 
                           'T1 Angle Comparison': tab3.CC_Angle_Segments_Tab, 
                           'AHA Model' : tab5.CC_AHA_Tab, 
                           'AHA Diff Model' : tab6.CC_AHA_Diff_Tab
                          }
        self.stats_tabs = {'Clinical Results' : tab2.CCs_ClinicalResults_Tab,
                           'Averaged AHA Tab' : tab7.CCs_AHA_Tab,
                           'Averaged AHA Diff Tab' : tab8.CCs_AHA_Diff_Tab, 
                           'Mapping Slice Analysis' : tab9.CCs_MappingSliceAnalysis_Tab}
        
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
        case.attach_clinical_results([SAXMap_GLOBALT1_PRE, NR_SLICES])
        # set new type
        case.type = self.ll_tag
        if debug: 
            print('Customization in SAX T1 PRE view took: ', time()-st)
            print('ending customize: ', case.case_name)
        return case
    
    def store_information(self, ccs, path, icon_path, storage_version=0):
        if storage_version>=0:
            try:
                cr_table = CC_ClinicalResultsAveragesTable()
                cr_table.calculate(ccs)
                crtol_p = cr_table.store(os.path.join(path, 'clinical_results_overview.csv'))
            except Exception as e:
                print(traceback.print_exc())
            try:
                overview_fig = Mapping_Overview()
                overview_fig.visualize(ccs, 'T1')
                ov_p = overview_fig.store(os.path.join(path))
            except Exception as e:
                print('Mapping Overview store exeption: ', traceback.print_exc())
            try:
                ref_fig = Reference_Point_Differences()
                ref_fig.visualize(ccs)
                ref_p = ref_fig.store(os.path.join(path))
            except Exception as e:
                print('Reference Differences store exeption: ', traceback.print_exc())
            try:
                t1aha_diff_fig = Statistical_T1_diff_bullseye_plot()
                t1aha_diff_fig.set_values(self, ccs, t1aha_diff_fig.canvas)
                t1aha_diff_fig.visualize()
                diffaha_p = t1aha_diff_fig.store(os.path.join(path))
            except Exception as e:
                print('T1 AHA DIFF store exeption: ', traceback.print_exc())
            try:
                cr_table = CCs_ClinicalResultsTable()
                cr_table.calculate(ccs)
                cr_table.store(os.path.join(path, 'clinical_results.csv'))
            except Exception as e:
                print('CR Table store exeption: ', traceback.print_exc())
            try:
                metrics_table = T1_CCs_MetricsTable()
                metrics_table.calculate(self, ccs)
                metrics_table.store(os.path.join(path, 'metrics_phase_slice_table.csv'))
            except Exception as e:
                print('Metrics Table store exeption: ', traceback.print_exc())
            try:
                failed_segmentation_folder_path = os.path.join(path, 'Failed_Segmentations')
                if not os.path.exists(failed_segmentation_folder_path): os.mkdir(failed_segmentation_folder_path)
                """
                failed_annotation_comparison = Failed_Annotation_Comparison_Yielder()
                failed_annotation_comparison.set_values(self, ccs)
                failed_annotation_comparison.store(failed_segmentation_folder_path)
                """
            except Exception as e:
                print(traceback.print_exc())
        
        if storage_version>=1:
            try:
                t1aha_r1_fig = Statistical_T1_bullseye_plot()
                t1aha_r1_fig.set_values(self, [cc.case1 for cc in ccs], t1aha_r1_fig.canvas)
                t1aha_r1_fig.visualize()
                r1aha_p = t1aha_r1_fig.store(os.path.join(path))
            except Exception as e:
                print('T1 AHA R1 store exeption: ', traceback.print_exc())
            try:
                t1aha_r2_fig = Statistical_T1_bullseye_plot()
                t1aha_r2_fig.set_values(self, [cc.case2 for cc in ccs], t1aha_r2_fig.canvas)
                t1aha_r2_fig.visualize()
                r2aha_p = t1aha_r2_fig.store(os.path.join(path))
            except Exception as e:
                print('T1 AHA R2 store exeption: ', traceback.print_exc())
        
        pdf = PDF(orientation='P', unit='mm', format='A4')
        
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                # CRs TABLE
                data = [l[1:] for l in csv.reader(open(os.path.join(path, 'clinical_results_overview.csv')), delimiter=';') if 'NrSlices' not in l[1]]
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        try:    data[i][j] = "{:10.2f}".format(float(data[i][j].replace(',','.')))
                        except: data[i][j] = data[i][j]
                pdf.set_title('Clinical Parameter Means and Tolerance Ranges')
                pdf.set_table(data[0:], x=15, y=30, col_widths=[40.0]+[30 for i in range(len(data[0])-2)]+[40.0])
                pdf.set_text("Table. 1 This table shows the clinical parameter names in the first column. The other columns show statistics concerning the parameters. The first and second readers' means (stds) are shown in the second and third column, respectively. The mean and std of the differences between both readers is presented in the fourth column. The mean difference of both readers ± 95% confidence intervals are shown in parentheses with ±tolerance ranges thereafter. This provides information on whether the 95% estimate of the mean difference between both readers is within an acceptable limit.", 10, 152)
            except: print(traceback.print_exc())
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title('Overview Assessment')
                pdf.set_chart(ov_p, 20, 35, w=695/4, h=841/4)
                pdf.set_text('Fig. 1 Overview of Mapping values and Contour Metrics: Bland-Altman plots for Mapping values as points for all cases / all slices (first /second row). Point size shows magnitude of difference, the solid line marks mean difference between readers, the dashed lines mark mean differences ±1.96 standard deviations. Paired Boxplots show Mapping values as assessed by the first reader (on top) and the second reader below for all cases / all slices (first / second row). Lines connect same cases / slices to one another. Row four contains a histogram and a tolerance range plot. The histogram shows nr of slices contoured by both readers / only first reader / only second reader or not by either. The tolerance range is shown for all slices segmented by both readers (excluding "overlooked" slices). The gray bars represent ±tolerance range. The ±95% confidence interval is plotted as an errorbar in red around the average difference. The case value differences are plotted in blue. In the fourth row (left) dice values are plotted per contour type. On the right Hausdorff distance values are plotted per contour type. Legend: Dice: Dice similarity coefficient, HD: Hausdorff distance', 10, 239, size=7)
            except: print(traceback.print_exc())
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title('Reference Point Differences')
                img = PIL.Image.open(ref_p)
                scale = img.height / img.width
                pdf.set_chart(ref_p, 20, 35, w=695/4, h=695/4*scale)
                pdf.set_text('Fig. 2 Reference Point Difference Plots: On the left the angle differences between readers per slice are plotted as a scatter plot on top of a boxplot. The angles are defined as the angle between the line between the endocardial median point and the reference point. On the right the distances between reference points selected by both readers are plotted as a scatter plot on top of a boxplot. Legend: mm: Millimeter', 10, 40 + 695/4*scale)
            except: print(traceback.print_exc())
        
        if storage_version>=1:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title(ccs[0].case1.reader_name + ' Avg AHA Model')
                img = PIL.Image.open(r1aha_p)
                scale = img.height / img.width
                pdf.set_chart(r1aha_p, 20, 35, w=695/4, h=695/4*scale)
                pdf.set_text('Fig. 3 Averages AHA Model: The AHA model is plotted for 16 segments reflecting the basal (6 outer segments), midventricular (6 middle segments) and apical (4 inner segments). Each segment contains a label with the mean ± standard deviation of the pixel values and the number of cases that provided values to the segment in parentheses. Legend: AHA: American Heart Association', 10, 40 + 695/4*scale)
            except: print(traceback.print_exc())

        if storage_version>=1:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title(ccs[0].case2.reader_name + ' Avg AHA Model')
                img = PIL.Image.open(r2aha_p)
                scale = img.height / img.width
                pdf.set_chart(r2aha_p, 20, 35, w=695/4, h=695/4*scale)
                pdf.set_text('Fig. 4 Averages AHA Model: The AHA model is plotted for 16 segments reflecting the basal (6 outer segments), midventricular (6 middle segments) and apical (4 inner segments). Each segment contains a label with the mean ± standard deviation of the pixel values and the number of cases that provided values to the segment in parentheses. Legend: AHA: American Heart Association', 10, 40 + 695/4*scale)
            except: print(traceback.print_exc())
        
        if storage_version>=0:
            try:
                pdf.add_page()
                pdf.prepare_pretty_format(icon_path)
                pdf.set_title('Avg Differences AHA Model')
                img = PIL.Image.open(diffaha_p)
                scale = img.height / img.width
                pdf.set_chart(diffaha_p, 20, 35, w=695/4, h=695/4*scale)
                pdf.set_text('Fig. 5 Average Differences AHA Model: The AHA model is plotted for 16 segments reflecting the basal (6 outer segments), midventricular (6 middle segments) and apical (4 inner segments). Each segment contains a label with the mean±standard deviation (n). The mean and standard deviation pertain to the pixel value differences per segmet between the two readers. In parentheses the number of cases that provided values to this segment by both readers is shown. Legend: AHA: American Heart Association', 10, 40 + 695/4*scale)
            except: print(traceback.print_exc())
        
        try:
            overviewtab = findCCsOverviewTab()
            view_name = type(self).__name__
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
        
        except Exception as e:
            print(traceback.print_exc())
            pass
        
        pdf.set_author('Luna Lovegood')
        pdf.output(os.path.join(path, view_name+'_summary_PDF.pdf'))
        