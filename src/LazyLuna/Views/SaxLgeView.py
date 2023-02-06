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
        case.attach_clinical_results([SAXLGE_LVV,         SAXLGE_LVMYOV, 
                                      SAXLGE_LVMYOMASS,   SAXLGE_SCARVOL,
                                      SAXLGE_SCARMASS,    SAXLGE_SCARF,
                                      SAXLGE_EXCLVOL,     SAXLGE_EXCLMASS,
                                      SAXLGE_NOREFLOWVOL, SAXLGE_NOREFLOWF])
        # set new type
        case.type = 'SAX LGE'
        if debug: print('Customization in SAX LGE view took: ', time()-st)
        return case


    def store_information(self, ccs, path, icon_path):
        try:
            overview_fig = LGE_Overview()
            overview_fig.visualize(ccs)
            ov_p = overview_fig.store(os.path.join(path))
        except Exception as e:
            print('Mapping Overview store exeption: ', traceback.print_exc())
        try:
            overview_fig = LGE_Overview_BySlice()
            overview_fig.visualize(ccs)
            ovbs_p = overview_fig.store(os.path.join(path))
        except Exception as e:
            print('Mapping Overview By Slice store exeption: ', traceback.print_exc())
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
        
            
        pdf = PDF(orientation='P', unit='mm', format='A4')
        
        try:
            pdf.add_page()
            pdf.prepare_pretty_format(icon_path)
            pdf.set_title('Overview Assessment')
            pdf.set_chart(ov_p, 20, 35, w=695/4, h=630/4)
            pdf.set_text("Fig. 1 Overview of Clinical Parameters: Upper left a Bland-Altman for the scar mass, upper right for the scar fraction defined as the volume of scar tissue divided by the volume of the left ventricular myocardium, middle left the mass of no reflow tissue, middle right the fraction of no reflow tissue defined as the volume of no reflow tissue divided by the volume of the left ventricular myocardium, the bottom left shows the left ventricular volume, and the left ventricle's myocardial mass on the botton right. Legend: Dice: Dice similarity coefficient, HD: Hausdorff distance", 10, 200, size=7)
        except: print(traceback.print_exc())
        
        try:
            pdf.add_page()
            pdf.prepare_pretty_format(icon_path)
            pdf.set_title('Overview Assessment')
            pdf.set_chart(ovbs_p, 20, 35, w=695/4, h=630/4)
            pdf.set_text('Fig. 2 Slice-based Overview of LGE values and Metrics as Scatter- ontop of Boxplots: Top left shows the scar area differences of all slices, top right the noreflow area differences, middle left the Dice of the LVM, middle right, the Dice of the scar contours, bottom left the Dice of no reflow contours, and the bottom right the distance of the reference points selected by the readers for individual slices. Legend: Dice: Dice similarity coefficient, LVM: Left ventricular myocardium', 10, 200, size=7)
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
        pdf.output(os.path.join(path, 'summary_PDF.pdf'))
        