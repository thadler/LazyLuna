from LazyLuna.Categories import *
from LazyLuna.ClinicalResults import *
from LazyLuna.Views.SaxT1PreView import SAX_T1_PRE_View

from LazyLuna.Tables  import *
from LazyLuna.Figures import *

import traceback


class SAX_T1_POST_View(SAX_T1_PRE_View):
    def __init__(self):
        super().__init__()
        self.ll_tag = 'SAX T1 POST'