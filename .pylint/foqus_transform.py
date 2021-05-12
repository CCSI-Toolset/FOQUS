###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
import astroid


def register(linter):
    """
    This function must be defined for pylint to use this module as a plugin.
    """


def get_pyqtsignal_classdef(context=None):
    src = (
        """
        class pyqtSignal:
            def __getitem__(self, key):
                return self
            def connect(self, slot, type=None, no_receiver_check=False):
                pass
            def disconnect(self, slot):
                pass
            def emit(self, *args):
                pass
        """
    )
    clsdef_node = astroid.extract_node(src)
    inferred_node = astroid.helpers.safe_infer(clsdef_node, context=context)
    return inferred_node


# add here names of pyQt signals incorrectly detected as normal attributes/bound methods
PYQTSIGNAL_ATTRIBUTE_NAMES = frozenset(
    [
        'currentIndexChanged',
    ]
)


def infer_signal_from_attribute(node: astroid.Attribute, context=None):
    signal_inst_node = get_pyqtsignal_classdef(context=context).instantiate_class()
    return iter([signal_inst_node])


def _is_attribute_actually_pyqtsignal(node: astroid.Attribute):
    return node.attrname in PYQTSIGNAL_ATTRIBUTE_NAMES


def _is_assign_attr_dat(node: astroid.AssignAttr):
    # TODO make this more specific, e.g. checking that the assigned value is None
    return node.attrname == 'dat'


def get_session_classdef(context=None):
    node = astroid.extract_node('from foqus_lib.framework.session.session import session; session')
    clsdef_node = astroid.helpers.safe_infer(node, context=context)
    return clsdef_node


def infer_session_for_attr(node: astroid.AssignAttr, context=None):
    inst_node = get_session_classdef(context=context).instantiate_class()
    return iter([inst_node])


astroid.MANAGER.register_transform(
    astroid.Attribute,
    astroid.inference_tip(infer_signal_from_attribute),
    _is_attribute_actually_pyqtsignal,
)


astroid.MANAGER.register_transform(
    astroid.AssignAttr,
    astroid.inference_tip(infer_session_for_attr),
    _is_assign_attr_dat,
)
