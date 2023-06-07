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


class AtDict(dict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name in list(self.keys()):
            self[name] = value
        else:
            super().__setattr__(name, value)


class OrderedAtDict(AtDict):
    def __init__(self, *args, **kwargs):
        self._ordered_keys = []
        super().__init__(self, *args, **kwargs)

    def __setitem__(self, name, value):
        if name not in self._ordered_keys:
            self._ordered_keys.append(name)
        super().__setitem__(name, value)

    def __delitem__(self, name):
        if name not in self._ordered_keys:
            return
        self._ordered_keys.remove(name)
        super().__delitem__(name)

    def __iter__(self):
        for k in self._ordered_keys:
            yield k

    def items(self):
        for k in self:
            yield (k, self[k])

    def ordered_keys(self):
        return self._ordered_keys
