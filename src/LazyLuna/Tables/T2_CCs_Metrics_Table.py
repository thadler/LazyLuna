import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *
from LazyLuna.Tables.T1_CCs_MetricsTable import *

class T2_CCs_Metrics_Table(T1_CCs_MetricsTable):
    def get_column_names(self, cat):
        n = cat.name
        return ['Casename', 'Slice', n+' Area Diff', n+' DSC', n+' HD', n+' T2avg_r1', n+' T2avg_r2', n+' T2avgDiff', n+' Insertion Point AngleDiff', n+' hascont1', n+' hascont2']

    