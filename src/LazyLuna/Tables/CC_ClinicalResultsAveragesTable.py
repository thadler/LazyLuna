import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *

import numpy as np


class CC_ClinicalResultsAveragesTable(Table):
    def calculate(self, case_comparisons):
        """Presents Clinical Results for the case_comparisons
        
        Note:
            Columns of mean±std for reader 1, reader 2, difference(reader1, reader2)
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): List of Case_Comparisons of two cases after View.customize_case(case) (for any View)
        """
        rows = []
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=['Clinical Result (mean±std)', case1.reader_name, case2.reader_name, 'Diff('+case1.reader_name+', '+case2.reader_name+')', '(Mean Diff±CI), ±Tol range']
        
        cr_dict1 = {cr.name+' '+cr.unit:[] for cr in case1.crs}
        cr_dict2 = {cr.name+' '+cr.unit:[] for cr in case1.crs}
        cr_dict3 = {cr.name+' '+cr.unit:[] for cr in case1.crs}
        cr_tolrange_dict = {cr.name+' '+cr.unit: cr.tol_range if hasattr(cr, 'tol_range') else np.nan for cr in case1.crs}
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            for cr1, cr2 in zip(c1.crs, c2.crs):
                cr_dict1[cr1.name+' '+cr1.unit].append(cr1.get_val())
                cr_dict2[cr1.name+' '+cr1.unit].append(cr2.get_val())
                cr_dict3[cr1.name+' '+cr1.unit].append(cr1.get_val_diff(cr2))
        rows = []
        for cr_name in cr_dict1.keys():
            row = [cr_name]
            row.append('{:.1f}'.format(np.nanmean(cr_dict1[cr_name])) + ' (' +
                      '{:.1f}'.format(np.nanstd(cr_dict1[cr_name])) + ')')
            row.append('{:.1f}'.format(np.nanmean(cr_dict2[cr_name])) + ' (' +
                      '{:.1f}'.format(np.nanstd(cr_dict2[cr_name])) + ')')
            row.append('{:.1f}'.format(np.nanmean(cr_dict3[cr_name])) + ' (' +
                      '{:.1f}'.format(np.nanstd(cr_dict3[cr_name])) + ')')
            mean = np.nanmean(cr_dict3[cr_name])
            ci   = 1.96 * np.nanstd(cr_dict3[cr_name]) / np.sqrt(len(cr_dict3[cr_name]))
            row.append('({:.1f}'.format(mean-ci) + ', {:.1f}'.format(mean+ci)+ '), ±{:.1f}'.format(cr_tolrange_dict[cr_name]))
            rows.append(row)
        self.df = DataFrame(rows, columns=columns)
        
        