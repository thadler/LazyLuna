import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class CC_StatsOverviewTable(Table):
    def get_dcm(self, cc):
        case = cc.case1
        for k in case.all_imgs_sop2filepath.keys():
            try: sop = next(iter(case.all_imgs_sop2filepath[k]))
            except: continue
            return pydicom.dcmread(case.all_imgs_sop2filepath[k][sop])
    def get_age(self, cc):
        try:
            age = self.get_dcm(cc).data_element('PatientAge').value
            age = float(age[:-1]) if age!='' else np.nan
        except: age=np.nan
        return age
    def get_gender(self, cc):
        try:
            gender = self.get_dcm(cc).data_element('PatientSex').value
            gender = gender if gender in ['M','F'] else np.nan
        except: gender=np.nan
        return gender
    def get_weight(self, cc):
        try:
            weight = self.get_dcm(cc).data_element('PatientWeight').value
            weight = float(weight) if weight is not None else np.nan
        except: weight=np.nan
        return weight
    def get_height(self, cc):
        try:
            h = self.get_dcm(cc).data_element('PatientSize').value
            h = np.nan if h is None else float(h)/100 if float(h)>3 else float(h)
        except: h=np.nan
        return h
    
    def calculate(self, ccs):
        """Calculates table with statistical overview of case comparisons, nr of case comparisons, genders, age etc.
        
        Note:
            columns are: [Nr Cases, Age (Y), Gender (M/F/Unknown), Weight (kg), Height (m)]
        
        Args:
            ccs (list of LazyLuna.Containers.Case_Comparison): list of case comparisons
        """
        columns = ['Nr Cases','Age (Y)','Gender (M/F/Unknown)','Weight (kg)','Height (m)']
        ages    = np.array([self.get_age(cc) for cc in ccs])
        genders = np.array([self.get_gender(cc) for cc in ccs])
        weights = np.array([self.get_weight(cc) for cc in ccs])
        heights = np.array([self.get_height(cc) for cc in ccs])
        rows = [[len(ccs), '{:.1f}'.format(np.nanmean(ages))+' ('+'{:.1f}'.format(np.nanstd(ages))+')', 
                str(np.sum(genders=='M'))+'/'+str(np.sum(genders=='F'))+'/'+str(int(np.sum([1 for g in genders if g not in ['M','F']]))), '{:.1f}'.format(np.nanmean(weights))+' ('+'{:.1f}'.format(np.nanstd(weights))+')', 
               '{:.1f}'.format(np.nanmean(heights))+' ('+'{:.1f}'.format(np.nanstd(heights))+')']]
        information_summary_df  = DataFrame(rows, columns=columns)
        self.df = information_summary_df
        