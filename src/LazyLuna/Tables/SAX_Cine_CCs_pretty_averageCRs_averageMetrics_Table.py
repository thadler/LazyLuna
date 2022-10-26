import pandas
from pandas import DataFrame
import traceback

from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *

from LazyLuna.Tables.Table import *
from LazyLuna.Tables.CC_CRTable import *
from LazyLuna.Tables.SAX_CINE_CCs_Metrics_Table import *


class SAX_Cine_CCs_pretty_averageCRs_averageMetrics_Table(Table):
    def calculate(self, case_comparisons, view):
        """Presents informative table (combination of CRs and Metric values) for a list of Case_Comparisons
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): contains a list of case comparisons
            view (LazyLuna.Views.View): a view for the analysis
        """
        cr_table = CCs_ClinicalResultsTable()
        cr_table.calculate(case_comparisons, with_metrics=True)
        means_cr_table = cr_table.df[['LVEF difference', 'LVEDV difference', 'LVESV difference', 'lv_endo avg dice', 
                             'lv_endo avg dice cont by both', 'lv_endo avg HD', 'LVM difference', 'lv_myo avg dice', 
                            'lv_myo avg dice cont by both', 'lv_myo avg HD', 'RVEF difference', 'RVEDV difference', 
                            'RVESV difference', 'rv_endo avg dice', 'rv_endo avg dice cont by both', 'rv_endo avg HD', 
                            'avg dice', 'avg dice cont by both', 'avg HD']].mean(axis=0)
        std_cr_table = cr_table.df[['LVEF difference', 'LVEDV difference', 'LVESV difference', 'lv_endo avg dice', 
                             'lv_endo avg dice cont by both', 'lv_endo avg HD', 'LVM difference', 'lv_myo avg dice', 
                            'lv_myo avg dice cont by both', 'lv_myo avg HD', 'RVEF difference', 'RVEDV difference', 
                            'RVESV difference', 'rv_endo avg dice', 'rv_endo avg dice cont by both', 'rv_endo avg HD', 
                            'avg dice', 'avg dice cont by both', 'avg HD']].std(axis=0)
        cr_table = pandas.concat([means_cr_table, std_cr_table], axis=1).reset_index()
        cr_table.columns = ['Name', 'Mean', 'Std']
        names = cr_table['Name']
        new_names = []
        for i, n in names.iteritems():
            n = n.replace(' difference', '').replace('avg HD','HD').replace('avg dice', 'Dice').replace('lv_endo', '').replace('rv_endo', '').replace('lv_myo','')
            if 'cont by both' in n: n = n.replace('cont by both', '(slices contoured by both)')
            elif 'Dice' in n:       n = n + ' (all slices)'
            if i>15:                     n = n + ' (all contours)'
            n = n.replace(') (', ', ')
            if 'HD' in n:                n = n + ' [mm]'
            if 'EF' in n or 'Dice' in n: n = n + ' [%]'
            if 'ESV' in n or 'EDV' in n: n = n + ' [ml]'
            if 'LVM' in n:               n = n + ' [g]'
            new_names.append(n)
        cr_table['Name'] = new_names
        self.cr_table = cr_table
        
        metrics_table = SAX_CINE_CCs_Metrics_Table()
        metrics_table.calculate(view, case_comparisons, pretty=False)
        metrics_table = metrics_table.df
        
        rows = []
        for position in ['basal', 'midv', 'apical']:
            # Precision = tp / tp + fp
            # Recall    = tp / tp + fn
            # dice all slices
            # dice by both
            row1, row2 = [position, 'Dice (all slices) [%]'], [position, 'Dice (slices contoured by both) [%]']
            row3, row4 = [position, 'HD [mm]'], [position, 'Abs. ml diff. (per slice) [ml]']
            for contname in ['lv_endo', 'lv_myo', 'rv_endo']:
                subtable = metrics_table[[k for k in metrics_table.columns if contname in k]]
                dice_ks     = [k for k in subtable.columns if 'DSC' in k]
                position_ks = [k for k in subtable.columns if 'Pos1' in k]
                all_dices = []
                for ki in range(len(dice_ks)): 
                    all_dices.extend([d for d in subtable[subtable[position_ks[ki]]==position][dice_ks[ki]]])
                row1.append(np.nanmean(all_dices))
                row2.append(np.nanmean([d for d in all_dices if 0<d<100]))
                hd_ks = [k for k in subtable.columns if 'HD' in k]
                hds   = []
                for ki in range(len(hd_ks)): hds.extend([d for d in subtable[subtable[position_ks[ki]]==position][hd_ks[ki]]])
                row3.append(np.nanmean(hds))
                # abs ml diff
                mld_ks = [k for k in subtable.columns if 'Abs ml Diff' in k]
                mlds   = []
                for ki in range(len(mld_ks)): mlds.extend([d for d in subtable[subtable[position_ks[ki]]==position][mld_ks[ki]]])
                row4.append(np.nanmean(mlds))
            rows.extend([row1, row2, row3, row4])
        self.metrics_table = DataFrame(rows, columns=['Position', 'Metric', 'LV Endocardial Contour', 'LV Myocardial Contour', 'RV Endocardial Contour'])
        #display(self.metrics_table)
        
    def present_metrics(self):
        self.df = self.metrics_table
    
    def present_crs(self):
        self.df = self.cr_table

        