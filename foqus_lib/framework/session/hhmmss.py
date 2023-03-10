#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
import math


def hhmmss(sec_in):
    # convert seconds to hh:mm:ss format
    h = int(sec_in // 3600)
    m = int(sec_in % 3600 // 60)
    s = sec_in % 3600 % 60
    if h < 24:
        hstr = "{0:0>2}".format(h)
    if h >= 24:
        hstr = "{0} days {1:0>2}".format(h // 24, h % 24)
    return "{0}:{1:0>2}:{2:0>2}".format(hstr, m, int(s))
