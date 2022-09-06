####################
# Clinical Results #
####################

from LazyLuna.Categories import *
import traceback

# decorator function for exception handling
def CR_exception_handler(f):
    def inner_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f.__name__ + ' failed to calculate the clinical result. Returning np.nan. Error traceback:')
            print(traceback.format_exc())
            return np.nan
    return inner_function


class Clinical_Result:
    def __init(self, case):
        self.case = case
        self.name = ''
        self.unit = '[]'
        self.tol_range = 0
    @CR_exception_handler
    def get_val(self, string=False):             pass
    def get_val_diff(self, other, string=False): pass

class LVSAX_ESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 7.3

    def set_CR_information(self):
        self.name = 'LVESV'
        self.unit = '[ml]'
        # MUST IMPORT CATEGORIES HERE
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('lv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_EDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 10.8

    def set_CR_information(self):
        self.name = 'LVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('lv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_ESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 9.7

    def set_CR_information(self):
        self.name = 'RVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('rv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_EDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 14.6

    def set_CR_information(self):
        self.name = 'RVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('rv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

# Phases
class LVSAX_ESPHASE(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVESP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        return str(self.cat.phase) if string else self.cat.phase

    def get_val_diff(self, other, string=False):
        p1, p2, nrp = self.get_val(), other.get_val(), self.cat.nr_phases
        cr_diff = min(abs(p1-p2), (min(p1,p2) - max(p1,p2)) % nrp) # module ring difference
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_EDPHASE(LVSAX_ESPHASE):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVEDP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

class RVSAX_ESPHASE(LVSAX_ESPHASE):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVESP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]

class RVSAX_EDPHASE(LVSAX_ESPHASE):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVEDP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

class NR_SLICES(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'NrSlices'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if hasattr(c, 'nr_slices')][0]

    @CR_exception_handler
    def get_val(self, string=False):
        return str(self.cat.nr_slices) if string else self.cat.nr_slices

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_MYO(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 13.3

    def set_CR_information(self):
        self.name = 'LVM'
        self.unit = '[g]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = 1.05 * self.cat.get_volume('lv_myo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_MYO(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVM'
        self.unit = '[g]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = 1.05 * self.cat.get_volume('rv_myo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_SV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 13.2

    def set_CR_information(self):
        self.name = 'RVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        esv = self.cat_es.get_volume('rv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('rv_endo', self.cat_ed.phase)
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_EF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 5.5

    def set_CR_information(self):
        self.name = 'RVEF'
        self.unit = '[%]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        esv = self.cat_es.get_volume('rv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('rv_endo', self.cat_ed.phase) + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_SV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 4.5

    def set_CR_information(self):
        self.name = 'LVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        esv = self.cat_es.get_volume('lv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('lv_endo', self.cat_ed.phase)
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_EF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        self.tol_range = 5.3

    def set_CR_information(self):
        self.name = 'LVEF'
        self.unit = '[%]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        esv = self.cat_es.get_volume('lv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('lv_endo', self.cat_ed.phase) + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

###########
# LAX CRs #
###########
########################
# LV Values:           #
# 4CV / 2CV / Biplane: #
# - ESV, EDV           #
# - SV,  EF            #
########################

#######
# 4CV #
#######
class LAX_4CV_LVESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LVEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr
        
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LVM(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LVM'
        self.unit = '[g]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        endo_area = self.cat.get_area('lv_lax_endo',  self.cat.phase)
        epi_area  = endo_area + self.cat.get_area('lv_lax_myo',  self.cat.phase)
        L         = self.cat.get_anno(0, self.cat.phase).length_LV()
        endo_area = 8/(3*np.pi) * (endo_area**2)/L / 1000
        epi_area  = 8/(3*np.pi) * (epi_area**2) /L / 1000
        cr        = 1.05 * (epi_area - endo_area)
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff



class LAX_4CV_LVSV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LVEF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LVEF'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000 + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_4CV_ESAtrialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_ES_Atrial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Atrial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_4CV_EDAtrialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_ED_Atrial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Atrial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_4CV_ESEpicardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_ES_Epicardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Epicardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_4CV_EDEpicardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_ED_Epicardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Epicardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_ESPericardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_ES_Pericardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Pericardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_4CV_EDPericardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_ED_Pericardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Pericardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff


# Phases
class LAX_4CV_LAESPHASE(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LAESP_4CV'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        return str(self.cat.phase) if string else self.cat.phase

    def get_val_diff(self, other, string=False):
        p1, p2, nrp = self.get_val(), other.get_val(), self.cat.nr_phases
        cr_diff = min(abs(p1-p2), (min(p1,p2) - max(p1,p2)) % nrp) # module ring difference
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
    
# Phases
class LAX_4CV_LAEDPHASE(LAX_4CV_LAESPHASE):
    def set_CR_information(self):
        self.name = 'LAEDP_4CV'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]
        
# Phases
class LAX_4CV_RAESPHASE(LAX_4CV_LAESPHASE):
    def set_CR_information(self):
        self.name = 'RAESP_4CV'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAES_Category)][0]
        
# Phases
class LAX_4CV_RAEDPHASE(LAX_4CV_LAESPHASE):
    def set_CR_information(self):
        self.name = 'RAEDP_4CV'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAED_Category)][0]
        
# Phases
class LAX_2CV_LAESPHASE(LAX_4CV_LAESPHASE):
    def set_CR_information(self):
        self.name = 'LAESP_2CV'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]
        
# Phases
class LAX_2CV_LAEDPHASE(LAX_4CV_LAESPHASE):
    def set_CR_information(self):
        self.name = 'LAEDP_2CV'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]


########
# 2 CV #
########
class LAX_2CV_LVESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LVEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LVM(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LVM'
        self.unit = '[g]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        endo_area = self.cat.get_area('lv_lax_endo',  self.cat.phase)
        epi_area  = endo_area + self.cat.get_area('lv_lax_myo',  self.cat.phase)
        L         = self.cat.get_anno(0, self.cat.phase).length_LV()
        endo_area = 8/(3*np.pi) * (endo_area**2)/L / 1000
        epi_area  = 8/(3*np.pi) * (epi_area**2) /L / 1000
        cr        = 1.05 * (epi_area - endo_area)
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_2CV_LVSV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LVEF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LVEF'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000 + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    

class LAX_2CV_ESAtrialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_ES_Atrial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Atrial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_2CV_EDAtrialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_ED_Atrial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Atrial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff    

class LAX_2CV_ESEpicardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_ES_Epicardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Epicardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_2CV_EDEpicardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_ED_Epicardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Epicardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_2CV_ESPericardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_ES_Pericardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Pericardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_2CV_EDPericardialFatArea(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_ED_Pericardial_Fat_Area'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('Pericardial', self.cat.phase)
        area = area / 100.0
        return "{:.2f}".format(area) if string else area

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

###########
# Biplane #
###########
class LAX_BIPLANE_LVESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE_LVESV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area1 = self.cat1.get_area('lv_lax_endo', self.cat1.phase)
        area2 = self.cat2.get_area('lv_lax_endo', self.cat2.phase)
        anno1 = self.cat1.get_anno(0, self.cat1.phase)
        anno2 = self.cat2.get_anno(0, self.cat2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_BIPLANE_LVEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE_LVEDV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area1 = self.cat1.get_area('lv_lax_endo', self.cat1.phase)
        area2 = self.cat2.get_area('lv_lax_endo', self.cat2.phase)
        anno1 = self.cat1.get_anno(0, self.cat1.phase)
        anno2 = self.cat2.get_anno(0, self.cat2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_BIPLANE_LVSV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE_LVSV'
        self.unit = '[ml]'
        self.cates1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cates2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cated1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]
        self.cated2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area1 = self.cates1.get_area('lv_lax_endo', self.cates1.phase)
        area2 = self.cates2.get_area('lv_lax_endo', self.cates2.phase)
        anno1 = self.cates1.get_anno(0, self.cates1.phase)
        anno2 = self.cates2.get_anno(0, self.cates2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        esv   = 8/(3*np.pi) * (area1*area2)/L / 1000
        area1 = self.cated1.get_area('lv_lax_endo', self.cated1.phase)
        area2 = self.cated2.get_area('lv_lax_endo', self.cated2.phase)
        anno1 = self.cated1.get_anno(0, self.cated1.phase)
        anno2 = self.cated2.get_anno(0, self.cated2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        edv   = 8/(3*np.pi) * (area1*area2)/L / 1000
        cr    = edv - esv
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_BIPLANE_LVEF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE_LVEF'
        self.unit = '[ml]'
        self.cates1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cates2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cated1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]
        self.cated2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area1 = self.cates1.get_area('lv_lax_endo', self.cates1.phase)
        area2 = self.cates2.get_area('lv_lax_endo', self.cates2.phase)
        anno1 = self.cates1.get_anno(0, self.cates1.phase)
        anno2 = self.cates2.get_anno(0, self.cates2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        esv   = 8/(3*np.pi) * (area1*area2)/L / 1000
        area1 = self.cated1.get_area('lv_lax_endo', self.cated1.phase)
        area2 = self.cated2.get_area('lv_lax_endo', self.cated2.phase)
        anno1 = self.cated1.get_anno(0, self.cated1.phase)
        anno2 = self.cated2.get_anno(0, self.cated2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        edv   = 8/(3*np.pi) * (area1*area2)/L / 1000 + 10**-9
        cr    = 100.0 * (edv - esv) / edv
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

################
# Right Atrium #
# - 4CV area   #
# - 4CV volume #
################

class LAX_4CV_RAESAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_RAESAREA'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_area('ra', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val() - other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_RAEDAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_RAEDAREA'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_area('ra', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_RAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_RAESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('ra', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_RA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_RAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_RAEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('ra', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_RA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
    
############
# LA 4CV   #
# - Area   #
# - Volume #
############
class LAX_4CV_LAESAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LAESAREA'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LAEDAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LAEDAREA'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LAESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV_LAEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
############
# LA 2CV   #
# - Area   #
# - Volume #
############
class LAX_2CV_LAESAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LAESAREA'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LAEDAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LAEDAREA'
        self.unit = '[cm^2]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LAESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV_LAEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]

    @CR_exception_handler
    def get_val(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
    
###############
# LA Biplanar #
# - Volume    #
###############
class LAX_BIPLANAR_LAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'BIPLANE_LAESV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        area1 = self.cat1.get_area('la', self.cat1.phase)
        L1    = self.cat1.get_anno(0, self.cat1.phase).length_LA()
        area2 = self.cat2.get_area('la', self.cat2.phase)
        L2    = self.cat2.get_anno(0, self.cat2.phase).length_LA()
        L     = min(L1, L2)
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_BIPLANAR_LAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'BIPLANE_LAEDV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        area1 = self.cat1.get_area('la', self.cat1.phase)
        L1    = self.cat1.get_anno(0, self.cat1.phase).length_LA()
        area2 = self.cat2.get_area('la', self.cat2.phase)
        L2    = self.cat2.get_anno(0, self.cat2.phase).length_LA()
        L     = min(L1, L2)
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff


###############
# CRs Mapping #
###############
class SAXMap_GLOBALT1(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'GLOBAL_T1'
        self.unit = '[ms]'
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        cr = []
        for d in range(self.cat.nr_slices):
            cr += self.cat.get_anno(d,0).get_pixel_values('lv_myo', self.cat.get_img(d,0)).tolist()
        cr = np.nanmean(cr)
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class SAXMap_GLOBALT2(SAXMap_GLOBALT1):
    def __init__(self, case):
        super().__init__(case)
        
    def set_CR_information(self):
        self.name = 'GLOBAL_T2'
        self.unit = '[ms]'
        self.cat  = self.case.categories[0]

class SAXLGE_LVV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'LVV'
        self.unit = '[ml]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
    
    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('lv_endo')
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class SAXLGE_LVMYOMASS(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'LVMMASS'
        self.unit = '[g]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        cr = 1.05 * self.cat.get_volume('lv_myo')
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class SAXLGE_LVMYOV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'LVMV'
        self.unit = '[ml]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('lv_myo')
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class SAXLGE_SCARMASS(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'SCARM'
        self.unit = '[g]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, contname='scar', string=False):
        #cr = 1.05 * self.cat.get_volume('scar_fwhm_res_8_excluded_area')
        cr = 1.05 * self.cat.get_volume(contname)
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, contname='scar', string=False):
        cr_diff = self.get_val(contname)-other.get_val(contname)
        return "{:.2f}".format(cr_diff) if string else cr_diff

class SAXLGE_SCARVOL(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'SCARV'
        self.unit = '[ml]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, contname='scar', string=False):
        #cr = self.cat.get_volume('scar_fwhm_res_8_excluded_area')
        cr = self.cat.get_volume(contname)
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, contname='scar', string=False):
        cr_diff = self.get_val(contname)-other.get_val(contname)
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class SAXLGE_SCARF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'SCARF'
        self.unit = '[%]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, contname='scar', string=False):
        #scar = self.cat.get_volume('scar_fwhm_res_8_excluded_area')
        scar = self.cat.get_volume(contname)
        lvm  = self.cat.get_volume('lv_myo')
        cr = 100.0 * (scar/(lvm+10**-9))
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, contname='scar', string=False):
        cr_diff = self.get_val(contname)-other.get_val(contname)
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class SAXLGE_EXCLMASS(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'EXCLMASS'
        self.unit = '[g]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        #scar_excl = self.cat.get_volume('scar_fwhm_res_8_excluded_area')
        #scar      = self.cat.get_volume('scar_fwhm_res_8')
        scar_excl = self.cat.get_volume('scar_fwhm_excluded_area')
        scar      = self.cat.get_volume('scar_fwhm')
        cr = 1.05 * (scar - scar_excl)
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
    
class SAXLGE_EXCLVOL(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'EXCLVOL'
        self.unit = '[ml]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
    
    @CR_exception_handler
    def get_val(self, string=False):
        scar_excl = self.cat.get_volume('scar_fwhm_res_8_excluded_area')
        scar      = self.cat.get_volume('scar_fwhm_res_8')
        cr = scar - scar_excl
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff
            
    
class SAXLGE_NOREFLOWVOL(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()
        
    def set_CR_information(self):
        self.name = 'NOREFLOWVOL'
        self.unit = '[ml]'
        #self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LGE_Category)][0]
        self.cat  = self.case.categories[0]
        
    @CR_exception_handler
    def get_val(self, string=False):
        cr = self.cat.get_volume('noreflow')
        return "{:.2f}".format(cr) if string else cr
    
    def get_val_diff(self, other, string=False):
        cr_diff = self.get_val()-other.get_val()
        return "{:.2f}".format(cr_diff) if string else cr_diff