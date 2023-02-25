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
import contextlib
from dataclasses import dataclass, field, asdict, is_dataclass
import enum
from functools import singledispatch
import logging
from pathlib import Path
import typing as t
from types import ModuleType
import time

try:  # available starting with Python 3.8
    from functools import singledispatchmethod
except ImportError:
    from singledispatchmethod import singledispatchmethod

import oyaml as yaml

# import yaml
from slugify import slugify

from PyQt5 import QtWidgets as W, QtCore, QtGui

from pytestqt import plugin as pytestqt_plugin
from _pytest.monkeypatch import MonkeyPatch


# NOTE these values can be given to aliases used as kwargs when an actual filter is not needed
# the actual value is a matter of synctactic sugar but it should suggest the meaning of
# "any result is fine, no need to filter since I expect it to be the only one"
KWARGS_PLACEHOLDER_VALUES = {True, any, next, ..., "*", ""}


_logger = logging.getLogger("pytest_qt_extras")


class _SerializableMixin:
    @classmethod
    def to_yaml(cls, dumper, obj):
        return dumper.represent_mapping(f"!{type(obj).__qualname__}", obj.as_record())

    def __str__(self):
        return self.dump()

    def as_record(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def dump(self):
        return yaml.dump(self, Dumper=yaml.Dumper)


def _object_to_yaml(dumper, obj):
    return dumper.represent_scalar(f"!{type(obj).__qualname__}", str(obj))


yaml.add_multi_representer(object, _object_to_yaml)
yaml.add_multi_representer(QtCore.QObject, _object_to_yaml)
yaml.add_multi_representer(_SerializableMixin, _SerializableMixin.to_yaml)


@singledispatch
def get_text(w: W.QWidget):
    raise NotImplementedError


@get_text.register
def _(btn: W.QAbstractButton):
    return btn.text().replace("&", "")


@get_text.register
def _(label: W.QLabel):
    return label.text()


@get_text.register
def _(group_box: W.QGroupBox):
    return group_box.title()


class ObjLogger:
    def __init__(self, **kwargs):
        self._logger_opts = kwargs

    def _get_logger_instance(self, cls: type):
        attr_name = "_logger"
        logger = getattr(cls, attr_name, None)
        if logger is None:
            name = cls.__qualname__
            logger = logging.getLogger(name, **self._logger_opts)
            setattr(logger, "__call__", logger.info)
            setattr(cls, attr_name, logger)
        return logger

    def __get__(self, obj, objtype=None):
        if obj is not None:
            return self._get_logger_instance(type(obj))
        return self._get_logger_instance(objtype)


@dataclass
class Action:
    name: str
    target: str
    args: tuple = None
    prose_template: str = None

    @property
    def readable_name(self):
        return self.name.capitalize().replace("_", " ")

    @property
    def description(self):
        if not self.args:
            return f"{self.name.title()} the {self.target}."
        return f"Using the {self.target}, {self.name} {_join(self.args)}."


class When(str, enum.Enum):
    BEGIN = "BEGIN"
    END = "END"


@dataclass
class CallInfo:
    callee: callable
    args: tuple
    kwargs: dict
    name: str
    instance: t.Optional[object] = None
    exception: t.Optional[Exception] = None
    result: t.Optional[object] = None
    parameters: dict = field(default_factory=dict)


@dataclass
class _WrappedCallable:
    wrapped: t.Callable = None
    name: str = None
    instance: object = None
    wrapper: t.Callable = None

    def matches_call(self, call: CallInfo) -> bool:
        return call.callee is self.wrapped and call.name == self.name


def _wrap_callable(
    func: t.Callable,
    call_begin: t.Callable[[CallInfo], t.Any],
    call_end: t.Callable[[CallInfo], t.Any],
) -> t.Callable[[t.Any], t.Any]:
    name = getattr(func, "__name__", None)
    instance = getattr(func, "__self__", None)
    is_bound_method = instance is not None

    def _wrapped(*args, **kwargs):
        info = CallInfo(
            callee=func,
            args=args,
            kwargs=kwargs,
            name=name,
            instance=instance,
            # parameters=signature.bind(*args, **kwargs)
        )
        call_begin(info)
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            info.exception = e
            raise e from None
        else:
            info.result = res
        finally:
            call_end(info)

    return _wrapped


@contextlib.contextmanager
def instrument(target, signal_begin=None, signal_end=None):
    mp = MonkeyPatch()

    _logger.info(f"instrumenting target {target}")
    if isinstance(target, tuple) and len(target) == 2:
        owner, name = target
        instance = None
    # TODO check if methodtype?
    else:
        instance = getattr(target, "__self__", None)
        owner = instance.__class__
        name = target.__name__
    func = getattr(owner, name)
    assert callable(func), f"{func} must be callable"
    _logger.debug(dict(target=target, name=name, owner=owner, func=func))

    def _do_nothing(*args, **kwargs):
        ...

    _patched_callable = _wrap_callable(
        func,
        call_begin=signal_begin.emit if signal_begin else _do_nothing,
        call_end=signal_end.emit if signal_end else _do_nothing,
    )

    mp.setattr(owner, name, _patched_callable)
    patched_info = _WrappedCallable(
        wrapped=func,
        name=name,
        instance=instance,
        wrapper=_patched_callable,
    )
    _logger.debug("returning patched object")
    yield patched_info
    _logger.debug("start undoing monkeypatching")
    mp.undo()
    _logger.debug("monkeypatching done")


@dataclass
class _DialogProxy:
    window_title: str = ""
    text: str = ""


@dataclass
class _ModalPatcher:

    dialog_cls: type
    scope: t.Optional[ModuleType] = None

    def __post_init__(self):
        if self.scope:
            assert isinstance(self.scope, ModuleType), (
                "If given, 'scope' should be a module object, "
                f"but it is {type(self.scope)} instead"
            )
        self._patch = MonkeyPatch()

    def _apply_patch(self, owner: object, name: str, replacement: object):
        self._patch.setattr(
            owner,
            name,
            replacement,
        )

    def _replace_entire_class(self, replacement: type):
        self._apply_patch(
            owner=self.scope, name=self.dialog_cls.__name__, replacement=replacement
        )

    def _replace_individual_methods(self, replacement: type, method_names: t.List[str]):
        for meth_name in method_names:
            self._apply_patch(
                owner=self.dialog_cls,
                name=meth_name,
                replacement=getattr(replacement, meth_name),
            )

    @contextlib.contextmanager
    def patching(self, dispatch_func: t.Callable):

        # TODO: consider if using type(...) to build the class object would make things clearer
        class tmp(self.dialog_cls):
            def exec_(inst):
                return dispatch_func(inst)

            def exec(inst):
                return dispatch_func(inst)

            def show(inst):
                dispatch_func(inst)

            def open(inst):
                dispatch_func(inst)

        if self.scope is not None:
            self._replace_entire_class(tmp)
        else:
            self._replace_individual_methods(
                tmp, method_names=["exec_", "exec", "show", "open"]
            )

        try:
            yield self
        finally:
            self._patch.undo()


@contextlib.contextmanager
def replace_with_signal(target, signal, retval=None):
    mp = MonkeyPatch()

    _logger.info(f"replacing target {target} with signal {signal}")
    if isinstance(target, tuple) and len(target) == 2:
        owner, name = target
        instance = None
    # TODO check if methodtype?
    else:
        instance = getattr(target, "__self__", None)
        owner = instance.__class__
        name = target.__name__
    func = getattr(owner, name)
    assert callable(func), f"{func} must be callable"
    _logger.debug(dict(target=target, name=name, owner=owner, func=func))

    def _proxy_call(*args, **kwargs):
        call_info = CallInfo(
            callee=func, args=args, kwargs=kwargs, name=name, instance=instance
        )

        signal.emit(call_info)

        return retval

    mp.setattr(owner, name, _proxy_call)

    patched_info = _WrappedCallable(
        wrapped=func,
        name=name,
        instance=instance,
        wrapper=_proxy_call,
    )

    _logger.debug("returning patched object")
    yield patched_info
    _logger.debug("start undoing monkeypatching")
    mp.undo()
    _logger.debug("monkeypatching done")


class _Signals(QtCore.QObject):
    __instance = None
    callBegin = QtCore.pyqtSignal(CallInfo)
    callEnd = QtCore.pyqtSignal(CallInfo)
    actionBegin = QtCore.pyqtSignal(Action)
    actionEnd = QtCore.pyqtSignal(Action)
    locateBegin = QtCore.pyqtSignal(object)
    locateEnd = QtCore.pyqtSignal(object)
    callProxy = QtCore.pyqtSignal(CallInfo)
    dialogDisplay = QtCore.pyqtSignal(_DialogProxy)

    @property
    def by_type_and_when(self):
        return {
            Action: {
                When.BEGIN: self.actionBegin,
                When.END: self.actionEnd,
            },
            CallInfo: {
                When.BEGIN: self.callBegin,
                When.END: self.callEnd,
            },
        }

    def __getitem__(self, key):
        return self.by_type_and_when[key]

    @classmethod
    def instance(cls) -> "_Signals":
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance


def _join(it, sep=" "):
    def is_to_skip(s):
        return str(s).strip() not in {str(None), ""}

    return str.join(sep, [str(_) for _ in it if not is_to_skip(_)])


def action(f):
    cls = Action
    signals = _Signals.instance()[cls]
    name = f.__name__

    def _wrapped(*args, **kwargs):
        handler = args[0]
        action = cls(name=name, target=handler.target, args=args[1:])
        signals[When.BEGIN].emit(action)
        f(*args, **kwargs)
        signals[When.END].emit(action)

    ...
    return _wrapped


class Dispatcher(_SerializableMixin):
    log = ObjLogger()

    def __init__(self, **kwargs):
        self.alias_map = kwargs

    def resolve_alias(self, kwargs: dict) -> t.Tuple[type, str]:
        alias_map = self.alias_map

        alias_in_kwargs: t.Set = kwargs.keys() & alias_map.keys()
        self.log.debug(f"alias_in_kwargs={alias_in_kwargs}")
        InvalidMatchError.check(alias_in_kwargs, expected=1)
        alias = alias_in_kwargs.pop()
        widget_cls = alias_map[alias]

        return widget_cls, alias

    @singledispatchmethod
    def get_target(self, widget: W.QWidget, **kwargs):
        return Target(widget, dispatcher=self, **kwargs)

    @singledispatchmethod
    def get_handler(self, widget, *args, **kwargs):
        return Handler(widget, *args, **kwargs)

    @get_handler.register
    def get_table_handler(self, widget: W.QTableWidget, *args, **kwargs):
        return TableHandler(widget, *args, **kwargs)

    @get_handler.register(list)
    def get_handler_from_list(self, widgets: t.List[W.QWidget], *args, **kwargs):
        return [self.get_handler(w, *args, **kwargs) for w in widgets]

    def as_record(self):
        return dict(self.alias_map)


# this should have as little behavior as possible that depends directly on the widget type
# we should be relying on stateless functions managed by singledispatch
class Handler(_SerializableMixin):
    log = ObjLogger()
    dispatcher = Dispatcher(
        button=W.QAbstractButton,
        radio_button=W.QRadioButton,
        combo_box=W.QComboBox,
        group_box=W.QGroupBox,
        table=W.QTableWidget,
        item_list=W.QListView,
        spin_box=W.QSpinBox,
        text_edit_area=W.QTextEdit,
        line_edit_area=W.QLineEdit,
    )

    def __init__(self, widget, located_by=None):
        self._widget = widget
        self._located_by = located_by

    @property
    def widget(self):
        return self._widget

    @property
    def target(self):
        """
        Here we can use some dispatch logic to create a human-readable summary of the widget and how it was located
        in the context of the action
        """
        return self.widget

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.dispatcher.get_handler(*args, **kwargs)

    def locate(self, *args, **kwargs):
        _logger.info(f"Starting locate for args: {args}, kwargs: {kwargs}")
        if not args:
            if not kwargs:
                raise ValueError
            widget_cls, alias = self.dispatcher.resolve_alias(kwargs)
            hint = kwargs.pop(alias)
            # locate(button=...)
            if hint in KWARGS_PLACEHOLDER_VALUES:
                hint = None
            # locate(button='Click here')
        else:
            if not len(args) in {1, 2}:
                raise ValueError(f"Invalid number of args specified")
            if len(args) == 1:
                # locate(QPushButton)
                target, hint = args[0], None
            else:
                # locate(QPushButton, 'Click here')
                target, hint = args

            if isinstance(target, W.QWidget):
                return self.create(target, located_by=None)
            elif isinstance(target, type) and issubclass(target, W.QWidget):
                widget_cls = target
            else:
                raise ValueError(f"Invalid type for target: {type(target)}")

        search = VisibleWidgetSearch.build(hint=hint, **kwargs)
        search.among_children(root=self.widget, widget_cls=widget_cls)
        search.summarize()
        result = search.result
        _logger.info(f"search result: {result}")
        return self.create(result, located_by=search)

    @action
    def click(self):
        self._click(self.widget)

    @singledispatchmethod
    def _click(self, button: W.QAbstractButton):
        button.click()

    @action
    def select(self):
        self._select(self.widget)

    @singledispatchmethod
    def _select(self, radio_button: W.QRadioButton):
        radio_button.click()

    @action
    def set_option(self, *args):
        self._set_option(self.widget, *args)

    @singledispatchmethod
    def _set_option(self, combo_box: W.QComboBox, text=str):
        matching_idx = combo_box.findText(text)
        if matching_idx == -1:
            raise NotEnoughMatchesError()
        combo_box.setCurrentIndex(matching_idx)

    @_set_option.register
    def _(self, list_box: W.QListWidget, text=str):
        matches = list_box.findItems(text, QtCore.Qt.MatchExactly)
        InvalidMatchError.check(matches, expected=1)
        list_box.setCurrentItem(matches[0])

    @action
    def enter_value(self, val):
        self._enter_value(self.widget, val)

    @singledispatchmethod
    def _enter_value(self, spin_box: W.QSpinBox, val):
        spin_box.setValue(val)

    @_enter_value.register
    def _(self, text_edit: W.QTextEdit, val):
        text_edit.setText(str(value))

    @action
    def select_tab(self, key: t.Union[int, str]):
        return self._select_tab(self.widget, key)

    def _select_tab(self, tabs: W.QTabWidget, text: str):
        for tab_idx in range(tabs.count()):
            tab_text = tabs.tabText(tab_idx)
            if text in tab_text:
                tabs.setCurrentIndex(tab_idx)
                return tab_idx

    def __repr__(self):
        return f"<{type(self).__name__}({self._widget})>"

    def as_record(self):
        return dict(widget=self.widget, located_by=self._located_by)


TableRowSpec = t.Union[int, str, None]
TableColumnSpec = t.Union[int, str]


@dataclass
class TableRowSearch(_SerializableMixin):
    hint: TableRowSpec
    idx: int
    count: int = None

    @classmethod
    def run(cls, table, hint: TableRowSpec):
        count = table.rowCount()

        if isinstance(hint, int):
            if hint < count:
                idx = hint
            else:
                raise InvalidMatchError(
                    f"row index {hint} out of range: (count: {count})"
                )
        elif hint is None:
            if count == 1:
                idx = 0
            else:
                hint = "currentRow"
                idx = table.currentRow()
        else:
            raise ValueError(f"Invalid hint: {hint!r}")

        return cls(hint=hint, idx=idx, count=count)


@dataclass
class TableColumnSearch(_SerializableMixin):
    hint: TableColumnSpec
    idx: int
    count: int = None
    name: str = None

    @classmethod
    def get_name(cls, table, idx):
        return table.horizontalHeaderItem(idx).text()

    @classmethod
    def run(cls, table, hint: TableColumnSpec):
        count = table.columnCount()
        name = None

        if isinstance(hint, int):
            if hint < count:
                idx = hint
            else:
                raise InvalidMatchError(
                    f"Column index {hint} out of range: (count: {count})"
                )
        elif isinstance(hint, str):
            name_by_idx = {i: cls.get_name(table, i) for i in range(count)}
            for idx, name in name_by_idx.items():
                if name == hint:
                    break
                idx = idx
                name = name
            else:
                raise InvalidMatchError(
                    f'Hint "{hint}" does not match any of {list(name_by_idx.values())}'
                )
        elif hint is None:
            if count == 1:
                idx = 0
        else:
            raise ValueError(f"Invalid hint: {hint!r}")

        return cls(
            hint=hint, idx=idx, name=name or cls.get_name(table, idx), count=count
        )


@dataclass
class TableCellSearch(_SerializableMixin):
    idx: t.Tuple[int, int]
    row_search: TableRowSearch
    column_search: TableColumnSearch
    widget: W.QWidget = None
    item: W.QTableWidgetItem = None

    @classmethod
    def run(cls, table, row, col):
        row_search = TableRowSearch.run(table, row)
        column_search = TableColumnSearch.run(table, col)
        idx = row_search.idx, column_search.idx

        widget = table.cellWidget(*idx)
        item = table.item(*idx)

        return cls(
            idx=idx,
            row_search=row_search,
            column_search=column_search,
            widget=widget,
            item=item,
        )

    @property
    def content(self):
        if self.widget is not None:
            return self.widget
        return self.item

    @property
    def row_idx(self):
        return self.idx[0]

    @property
    def column_idx(self):
        return self.idx[1]


class TableHandler(Handler):
    @property
    def table(self) -> W.QTableWidget:
        return self.widget

    @action
    def select_row(self, row: TableRowSpec):
        search = TableRowSearch.run(self.table, row)
        self.table.selectRow(search.idx)
        _logger.debug(f"self.table.currentRow()={self.table.currentRow()}")
        _logger.debug(f"self.table.currentColumn()={self.table.currentColumn()}")

    @action
    def select_cell(self, row: TableRowSpec, col: TableColumnSpec):
        search = TableCellSearch.run(self.table, row, col)
        self.table.setCurrentCell(*search.idx)

    @action
    def select(self, row: TableRowSpec = None, col: TableColumnSpec = 0):
        self.select_cell(row, col)

    def has_matching_row(self, row_spec: dict):
        for row_idx in range(self.table.rowCount()):
            row_matches = {}
            for key, val in row_spec.items():
                # TODO check if column exists
                col_idx = self._get_col_idx(key)
                value_in_row = self._get_cell_content(col_idx, row_idx)
                row_matches[key] = value_in_row == val
            entire_row_matches = all(row_matches.values())
            if entire_row_matches:
                return row_idx

    def locate(
        self, row: TableRowSpec = None, column: TableColumnSpec = None, **kwargs
    ):
        "Locate a widget within (i.e. in a cell of) the table."
        if column is None and len(kwargs) == 1:
            column = set(kwargs.values()).pop()
        cell_match = TableCellSearch.run(self.table, row, column)
        _logger.debug(f"cell_match: {cell_match}")
        return self.create(cell_match.content, located_by=cell_match)


class TreePath:
    def __init__(self, indices: t.Iterable[int] = None):
        self._indices = list(indices or [])

    def with_appended(self, idx):
        return type(self)(self._indices + [idx])

    def __iter__(self):
        return iter(self._indices)

    def __str__(self):
        return str.join(".", [str(i) for i in self])

    @classmethod
    def root(cls):
        return cls([0])


@dataclass
class WidgetDecoration(_SerializableMixin):
    rect: QtCore.QRect
    text: str = None
    color: t.Any = None


@dataclass
class TextOnOffsetLabel(WidgetDecoration):
    line_width: int = 2
    line_style: t.Any = QtCore.Qt.SolidLine
    text_color: t.Any = QtCore.Qt.white
    text_align: t.Any = QtCore.Qt.AlignCenter

    def make_text_box(self, text_height: int):
        return self.rect.adjusted(0, -text_height, 0, -self.rect.height())

    def draw_rect(self, painter):
        painter.setPen(QtGui.QPen(self.color, self.line_width, self.line_style))
        painter.drawRect(self.rect)

    def draw_text(self, painter, text_height):
        pen = QtGui.QPen(self.text_color)
        text_box = self.make_text_box(text_height)
        painter.fillRect(text_box, self.color)
        painter.drawRect(text_box)
        painter.setPen(pen)
        painter.drawText(text_box, self.text_align, self.text)

    def __call__(self, painter, text_height):
        self.draw_rect(painter)
        if self.text:
            self.draw_text(painter, text_height)


class Annotations(W.QWidget):
    @classmethod
    def from_widget(cls, w, color=None, **kwargs):
        self = cls(color=color)
        cls.add(w, **kwargs)
        return cls

    def __init__(self, parent=None, color=QtCore.Qt.gray):
        super().__init__(parent=parent)
        self._items = {}
        self._window = None
        self.color = color
        self.text_height = self.fontMetrics().ascent()

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, win):
        self._window = win
        self.setParent(win)
        self.setGeometry(win.rect())

    def get_rect(self, w: W.QWidget):
        orig = w.rect()
        topleft_wrt_window = w.mapTo(self.window, orig.topLeft())
        return orig.translated(topleft_wrt_window)

    @contextlib.contextmanager
    def updating_once(self):
        old_update = self.update
        self.update = lambda *a, **kw: None
        yield self
        self.update = old_update
        self.update()

    def add_widgets(self, *widgets, make_decoration=None, color=None, **kwargs):
        self.window = widgets[0].window()
        make_decoration = make_decoration or TextOnOffsetLabel
        for w in widgets:
            key = id(w)
            self._items[key] = make_decoration(
                rect=self.get_rect(w), color=color or self.color, **kwargs
            )
        self.update()

    @singledispatchmethod
    def add(self, widget: W.QWidget, **kwargs):
        self.add_widgets(widget, **kwargs)

    @singledispatchmethod
    def remove(self, key):
        del self._items[key]
        self.update()

    @remove.register
    def remove_widget(self, w: W.QWidget):
        self.remove(id(w))

    @add.register
    def add_action(self, action: Action, **kwargs):
        self.add(
            action.target,
            text=action.readable_name,
            make_decoration=TextOnOffsetLabel,
            **kwargs,
        )

    @remove.register
    def remove_action(self, action: Action):
        self.remove(action.target)

    def paintEvent(self, ev):
        painter = QtGui.QPainter()
        painter.begin(self)
        for deco in self._items.values():
            deco(painter, text_height=self.text_height)
        painter.end()


@dataclass
class WidgetInfo:
    id_: str
    type_: type = None
    parent: str = None
    text: str = None
    is_visible: bool = None
    # tree_path: TreePath = None
    geometry: t.Any = None
    children: t.Dict = None
    _widget: W.QWidget = None

    @property
    def abbrev(self):
        return f"{self.type_}(...{self.id_[-5:]})"

    @classmethod
    def link_display(cls, w):
        return cls(id_=str(hex(id(w))), type_=type(w).__qualname__).abbrev

    @singledispatchmethod
    @classmethod
    def collect(cls, w: W.QWidget, parent=None, children=None, **kwargs):
        id_ = str(hex(id(w)))
        type_ = type(w).__qualname__
        info = cls(
            id_=id_,
            type_=type_,
        )
        if parent:
            info.parent = cls.link_display(parent)

        if children:
            info.children = {
                i: cls.link_display(child) for i, child in enumerate(children)
            }

        if isinstance(w, W.QWidget):
            info.is_visible = w.isVisible()
            try:
                info.text = get_text(w)
            except Exception as e:
                pass

        return info

    @classmethod
    def walk(cls, w: W.QWidget, tree_path=None, parent=None, collect=None):
        collect = collect or cls.collect
        tree_path = tree_path or TreePath.root()
        children = w.children()
        info = collect(w, parent=parent, children=children, tree_path=tree_path)
        yield tree_path, info
        for idx, child in enumerate(children):
            yield from cls.walk(
                child, tree_path=tree_path.with_appended(idx), parent=w, collect=collect
            )

    def items_to_publish(self):
        for k, v in self.__dict__.items():
            if v is None or k.startswith("_"):
                continue
            yield k, v

    def as_record(self):
        return dict(self.items_to_publish())


class HierarchyInfo(_SerializableMixin):
    def __init__(self, root: W.QWidget):
        self._root = root
        self._items = None

    def collect(self, w: W.QWidget, **kwargs):
        info = WidgetInfo.collect(w, **kwargs)
        info._widget = w
        return info

    def __iter__(self):
        if self._items is None:
            self._items = list(WidgetInfo.walk(self._root, collect=self.collect))
        return iter(self._items)

    def as_record(self):
        return {str(path): info.as_record() for path, info in self}

    @contextlib.contextmanager
    def annotating(self):
        known_classes = tuple(Handler.dispatcher.alias_map.values())
        paths = []
        try:
            mann = Annotations(color=QtCore.Qt.blue)
            for path, info in self:
                path = str(path)
                if info.is_visible and isinstance(info._widget, known_classes):
                    mann.add(info._widget, text=path, text_align=QtCore.Qt.AlignRight)
                    # ann = Annotation.create(
                    #     info._widget, text=path, color=QtCore.Qt.darkRed,
                    # )
                    paths.append(path)
                    # ann.show()

            mann.show()
            # yield annotations
            yield mann
        except Exception as e:
            _logger.exception(e)
        finally:
            mann.hide()
            mann.deleteLater()
            # for ann in annotations.values():
            #     ann.deleteLater()


class InvalidMatchError(ValueError):
    @classmethod
    def check(cls, found: t.Iterable, expected: int = 1, **kwargs):
        found = list(found)
        n_found = len(found)
        if n_found == expected:
            return True
        exc = NotEnoughMatchesError if n_found < expected else TooManyMatchesError
        raise exc(expected=expected, found=found, **kwargs)

    def __init__(self, *args, explain: t.Callable = (lambda: None), **kwargs):
        super().__init__(*args)
        self.kwargs = kwargs
        self.explain = explain

    def __str__(self):
        self.explain()
        return super().__str__()


class NotEnoughMatchesError(InvalidMatchError):
    pass


class TooManyMatchesError(InvalidMatchError):
    pass


class Selection(_SerializableMixin):
    @classmethod
    def from_locals(cls, data):
        "Make it easier to collect variables from a function scope using locals()"
        to_collect = {
            k: v for k, v in data.items() if not (k.startswith("_") or k in {"self"})
        }
        return cls(**to_collect)

    def __init__(
        self,
        is_match: bool = None,
        cand: t.Any = None,
        error: Exception = None,
        **kwargs,
    ):
        self.is_match = is_match
        self.cand = cand
        self.error = error
        self.info = kwargs

    def __bool__(self):
        return bool(self.is_match)

    def __repr__(self):
        s = f"{type(self).__name__}({bool(self)}, cand={self.cand}, error={self.error}, info={self.info})"
        return s


class Selector(_SerializableMixin):
    log = ObjLogger()
    "Applies a select callable to multiple candidates and stores the resulting Selection instances."

    def __init__(self, func: t.Callable):
        self._func = func
        self._candidates: t.Iterable = None
        self._selections: t.Iterable[Selection] = []
        self._matching: t.Iterable = []

    def __call__(self, candidates: t.Iterable) -> t.Iterable:
        self._candidates = list(candidates)
        for cand in self._candidates:
            sel = self.apply(cand)
            self.log.debug(str(sel))
            self._selections.append(sel)

        self._matching = [sel.cand for sel in self._selections if sel]

        return list(self._matching)

    def apply(self, cand):
        "Apply self._func to a single candidate and store the result in a Selection object."

        try:
            res = self._func(cand)
        except Exception as e:
            return Selection(error=e)
        else:
            if isinstance(res, Selection):
                sel = res
            elif isinstance(res, bool):
                sel = Selection(is_match=res, cand=cand)
            else:
                raise ValueError(
                    f"Invalid type returned by callable {self._func}: {type(res)}"
                )
        return sel

    @property
    def matching(self):
        return self._matching

    def __iter__(self):
        return iter(self._matching)

    def __len__(self):
        return len(self._matching)

    def __bool__(self):
        return len(self) > 0

    def as_record(self):
        return dict(
            func=self._func,
            candidates=list(self._candidates),
            matching=list(self.matching),
        )

    # def __str__(self):
    #     lines = [f'{type(self).__name__}(func={self._func})']
    #     def gen_seq_display(seq, name):
    #         yield f'\t{name}: {len(seq)}'
    #         for item in seq:
    #             yield f'\t\t{item}'
    #     lines.extend(gen_seq_display(self._candidates, 'candidates'))
    #     lines.extend(gen_seq_display(self._matching, 'matching'))
    #     return str.join('\n', lines)


class Search(_SerializableMixin):
    def __init__(self, selectors=None, result_key=None):
        self._selectors = []
        self._candidates: t.Iterable = None
        self._matching: t.Iterable = None
        self._result_key = result_key
        self.info = {}

        for sel in selectors or []:
            self.add(sel)

    @property
    def selectors(self) -> t.Iterable[Selector]:
        return self._selectors

    def add(self, maybe_sel, **kwargs):
        selector = (
            maybe_sel if isinstance(maybe_sel, Selector) else Selector(func=maybe_sel)
        )
        self._selectors.append(selector)
        self.info.update(kwargs)

    def __iter__(self) -> t.Iterable:
        return iter(self.selectors)

    def __call__(self, candidates: t.Iterable) -> t.Iterable:
        self._candidates = candidates = list(candidates)

        for sel in self:
            try:
                matching = sel(candidates)
                # assert len(matching) >= 1
            except Exception as e:
                _logger.exception(e)
            else:
                candidates = self._matching = matching

    @property
    def matching(self):
        return self._matching

    @property
    def stats(self):
        return dict(n_candidates=len(self._candidates), n_matching=len(self.matching))

    def summarize(self, dump=True):
        _logger.info(f"{self!r}")
        _logger.info(self.stats)
        if not self.matching:
            _logger.warning("No matches found")
            if dump:
                _logger.info(self.dump())

    @property
    def result(self):
        return self.get(key=self._result_key)

    def get(self, key=None, fallback=None):
        matching = list(self.matching)
        if key in [None]:
            InvalidMatchError.check(matching, expected=1)
            return matching[0]
        if isinstance(key, int):
            assert 0 <= key <= len(matching)
            return matching[key]
        else:
            # assume is a sequence of integers to be used to index multiple items
            return [matching[idx] for idx in key]

    def as_record(self):
        return dict(
            selectors=list(self.selectors),
            info=dict(self.info),
            n_candidates=len(self._candidates),
            matching=list(self.matching),
            result_key=self._result_key,
            result=self.result,
        )


@get_text.register(W.QComboBox)
@get_text.register(W.QSpinBox)
def from_sibling_labels(target: W.QWidget, direction="E"):
    def has_nonempty_text(cand: W.QWidget):
        text = get_text(cand)

        return Selection(is_match=(text != ""), cand=cand, text=text)

    def is_related_by_proximity(cand: W.QWidget):
        # the geometries are directly comparable because the widgets are siblings
        tgt_geom = target.geometry()
        cand_geom = cand.geometry()

        tgt_left = tgt_geom.left()
        cand_right = cand_geom.right()
        horizontal_distance = tgt_left - cand_right
        is_cand_preceeding_horizontally = horizontal_distance >= 0

        tgt_top, tgt_btm = tgt_geom.top(), tgt_geom.bottom()
        cand_top, cand_btm = cand_geom.top(), cand_geom.bottom()

        is_cand_completely_above = cand_btm < tgt_top
        is_cand_completely_below = cand_top > tgt_btm
        has_partial_vertical_overlap = not (
            is_cand_completely_above or is_cand_completely_below
        )

        is_match = is_cand_preceeding_horizontally and has_partial_vertical_overlap

        return Selection.from_locals(locals())

    def refers_to_other_widgets(w: W.QLabel):
        return isinstance(w, W.QLabel)

    search = Search(
        selectors=[refers_to_other_widgets, has_nonempty_text, is_related_by_proximity]
    )
    parent = target.parent()
    # we only search for labels among the immediate (non-recursive) siblings
    siblings = parent.children()
    search(siblings)
    # there can be more than one label matching
    # this is in principle OK at this level, and should be dealt with at the level of the text matcher
    # another option is to sort the list so that the closest to the target (defined in e.g. horizontal distance) is returned
    InvalidMatchError.check(search.matching, expected=1)
    matching_label = search.result

    return get_text(matching_label)


@dataclass
class VisibleTextMatcher(_SerializableMixin):
    hint: str
    extract: t.Callable[[t.Any], str] = str
    transform: t.Callable[[str], str] = str
    compare: t.Callable[[str, str], bool] = str.__eq__
    # these might be stored mainly for reference depending on whether they're used after building compare() and transform()
    case_sensitive: bool = None
    truncation_symbol: str = None

    @classmethod
    def build(
        cls,
        hint: str,
        case_sensitive: t.Union[str, bool] = "smart",
        truncation_symbol: str = "[...]",
        **kwargs,
    ):
        if case_sensitive == "smart":
            case_sensitive = hint.casefold() != hint

        transform = str if case_sensitive else str.casefold
        compare = cls._get_compare_func(hint, truncation_symbol)

        return cls(
            hint=hint,
            transform=transform,
            compare=compare,
            case_sensitive=case_sensitive,
            truncation_symbol=truncation_symbol,
            **kwargs,
        )

    @classmethod
    def _get_compare_func(cls, hint, truncation_symbol):
        if hint.startswith(truncation_symbol) and hint.endswith(truncation_symbol):
            op = str.__contains__
        elif hint.endswith(truncation_symbol):
            op = str.startswith
        elif hint.startswith(truncation_symbol):
            op = str.endswith
        else:
            op = str.__eq__
        return op

    def __call__(self, cand):
        text_to_search_for = self.hint.replace(self.truncation_symbol, "")
        extracted = self.extract(cand)
        text_to_search_in = str(extracted)

        is_match = self.compare(
            self.transform(text_to_search_in), self.transform(text_to_search_for)
        )

        return Selection.from_locals(locals())


def is_visible(w: W.QWidget):
    return w.isVisible()


def is_enabled(w: W.QWidget):
    return w.isEnabled()


class VisibleWidgetSearch(Search):
    @classmethod
    def build(cls, hint=None, require_enabled=None, index=None, **kwargs):
        self = cls(result_key=index, **kwargs)

        self.add(is_visible)

        if require_enabled:
            self.add(is_enabled, require_enabled=True)
        if hint is not None:
            text_matcher = VisibleTextMatcher.build(hint, extract=get_text)
            self.add(text_matcher, hint=hint)

        return self

    def among_children(self, root: W.QWidget, widget_cls=W.QWidget):
        self.info.update(root=root, widget_cls=widget_cls)
        candidates = root.findChildren(widget_cls)
        return self(candidates)


class _TestArtifact:
    def __init__(self, label=None):
        self._label = label

    @property
    def label(self):
        return self._label

    def save(self, path: Path):
        raise NotImplementedError


class ArtifactManager:
    def __init__(self, base_path: Path, save_later=False):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._items = []
        self.save_later = save_later

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def create_offshoot(self, name, **kwargs):
        opts = dict(save_later=self.save_later)
        opts.update(kwargs)
        return type(self)(self.base_path / name, **opts)

    def add(self, item: _TestArtifact):
        self._items.append(item)
        if not self.save_later:
            self.save(item)

    def save(self, item: _TestArtifact):
        item_dir = Path(self.base_path)
        progressive_id = len(self)
        filename = slugify(f"{progressive_id}-{item.label}")
        item_path = item_dir / filename
        try:
            return item.save(item_path)
        except Exception as e:
            _logger.error(f"Error while saving artifact at {item_path}")
            _logger.exception(e)
        else:
            _logger.info(f"Saved artifact at {item_path}")

    def save_all(self):
        for item in self:
            self.save_item(item)


class Snapshot(_TestArtifact):
    @classmethod
    def from_widget(
        cls,
        widget: W.QWidget,
        entire_window=True,
        hierarchy_info=False,
        annotate=False,
        **kwargs,
    ):
        to_grab = widget.window() if entire_window else widget
        pixmap = to_grab.grab()

        if hierarchy_info:
            info = HierarchyInfo(widget)
            kwargs["data"] = info
            if annotate:
                with info.annotating():
                    pixmap = to_grab.grab()

        return cls(pixmap=pixmap, **kwargs)

    def __init__(
        self,
        pixmap: QtGui.QPixmap = None,
        text: str = None,
        data: t.Any = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._pixmap = pixmap
        self.text = text
        self.data = data

    def save(self, path: Path):
        if self._pixmap is None:
            _logger.warning(f"No pixmap to save for {self}")
        else:
            self._pixmap.save(path.with_suffix(".png").__fspath__())
        if self.text:
            path.with_suffix(".txt").write_text(self.text)
        if self.data:
            path.with_suffix(".yml").write_text(
                yaml.dump(self.data, Dumper=yaml.Dumper)
            )


class QtBot(pytestqt_plugin.QtBot):
    "Extends original class with a few convenience methods"
    log = ObjLogger()

    def __init__(
        self,
        *args,
        focused: W.QWidget = None,
        slowdown_wait=500,
        artifacts: t.Optional[t.Union[bool, Path]] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._dispatcher = None
        self._focus_stack = []

        self.focused = focused or W.QApplication.instance().activeWindow()

        self._slowdown_wait = slowdown_wait
        self.annotations = Annotations()

        self._artifacts = artifacts

        if self._artifacts:
            artifacts_path = Path(artifacts).resolve()
            self._screenshots = ArtifactManager(artifacts_path / "screenshots")
            self._snapshots = ArtifactManager(artifacts_path / "snapshots")

        self._signals = _Signals.instance()
        self._init_signals()

    def _init_signals(self):
        # self._signals[Action][When.BEGIN].connect(lambda a: _logger.info(f'Action started: {a}'))
        # self._signals[Action][When.END].connect(lambda a: _logger.info(f'Action ended: {a}'))
        self._signals[Action][When.BEGIN].connect(self.on_action_begin)
        self._signals[Action][When.END].connect(self.on_action_end)

    def on_action_begin(self, action: Action):
        _logger.info(f"Begin: {action}")
        self.annotations.add(action, color=QtCore.Qt.red)
        self.annotations.show()
        # action.begin_annotate()
        self.slow_down()

    def on_action_end(self, action: Action):
        _logger.info(f"End: {action}")
        # self.slow_down()
        self.annotations.remove(action)
        # action.end_annotate()

    def slow_down(self):
        self.wait(self._slowdown_wait)

    def take_screenshot(self, label, **kwargs):
        if not self._artifacts:
            return
        shot = Snapshot.from_widget(self.focused, label=label, **kwargs)
        self._screenshots.add(shot)

    def take_debug_snapshot(self, label, **kwargs):
        if not self._artifacts:
            return
        debug_shot = Snapshot.from_widget(
            self.focused, label=label, annotate=True, hierarchy_info=True, **kwargs
        )
        self._snapshots.add(debug_shot)

    def describe(self):
        pass

    @contextlib.contextmanager
    def taking_screenshots(self, actions=True):
        take_scr = self.take_screenshot

        def take_scr(action: Action, when):
            if not self._artifacts:
                return
            widget = action.target
            for_window = Snapshot.from_widget(
                widget=widget, label=f"{when}-{action.description}"
            )
            for_widget = Snapshot.from_widget(
                widget=widget,
                entire_window=False,
                label=f"{when}-{action.description}-widget-only",
            )
            self._screenshots.add(for_window)

        on_action_begin = lambda a: take_scr(a, "before")
        on_action_end = lambda a: take_scr(a, "after")

        signals = self._signals[Action]
        signals[When.BEGIN].connect(on_action_begin)
        signals[When.END].connect(on_action_end)

        try:
            yield take_scr
        finally:
            signals[When.BEGIN].disconnect(on_action_begin)
            signals[When.END].disconnect(on_action_end)

    @property
    def focused(self) -> W.QWidget:
        return self._focus_stack[-1]

    @focused.setter
    def focused(self, new: W.QWidget):
        self._focus_stack.append(new)

    @focused.deleter
    def focused(self):
        self._focus_stack.pop(-1)

    @property
    def handler(self):
        return Handler.create(self.focused)

    def get_handler(self, *args, **kwargs):
        if not (args or kwargs):
            return self.handler
        if len(args) == 1 and isinstance(args[0], Handler):
            handler = args[0]
            return handler
        return self.locate(*args, **kwargs)

    using = get_handler

    def locate(self, *args, **kwargs):
        self.slow_down()
        try:
            self.take_debug_snapshot(label=f"locate-{args}-{kwargs}")
            res = self.handler.locate(*args, **kwargs)
        except InvalidMatchError as e:
            self.log.error(f"Invalid match for locate({args, kwargs})")
            self.log.exception(e)
            raise e
        return res

    def locate_widget(self, *args, **kwargs):
        return self.locate(*args, **kwargs).widget

    @contextlib.contextmanager
    def switching_focused(self, *args, **kwargs):
        new = self.locate_widget(*args, **kwargs)
        self.focused = new
        try:
            yield new
        finally:
            del self.focused

    focusing_on = searching_within = switching_focused

    def click(self, *args, **kwargs):
        return self.get_handler(*args, **kwargs).click()

    def set_option(self, val, *args, **kwargs):
        return self.get_handler(*args, **kwargs).set_option(val)

    def enter_value(self, val, *args, **kwargs):
        return self.get_handler(*args, **kwargs).enter_value(val)

    def select(self, *args, **kwargs):
        return self.get_handler(*args, **kwargs).select()

    def select_row(self, row, *args, **kwargs):
        return self.get_handler(*args, **kwargs).select_row(row)

    def select_tab(self, tab_name, *args, **kwargs):
        return self.get_handler(W.QTabWidget).select_tab(tab_name)

    @contextlib.contextmanager
    def instrumenting(self, func):
        signals = self._signals[CallInfo]
        with instrument(
            func, signal_begin=signals[When.BEGIN], signal_end=signals[When.END]
        ) as instrumented:
            instrumented.signals = signals
            yield instrumented

    def wait_until_called(self, func, before=False, **kwargs):
        wait_for = When.BEGIN if before else When.END

        with self.instrumenting(func) as instrumented:
            self.wait_signal(
                instrumented.signals[wait_for],
                check_params_cb=instrumented.matches_call,
                **kwargs,
            )

    @contextlib.contextmanager
    def replacing_with_signal(
        self, *targets: t.Iterable[t.Union[t.Callable, t.Tuple[type, str]]], **kwargs
    ):
        signal = self._signals.callProxy
        with contextlib.ExitStack() as stack:
            [
                stack.enter_context(
                    replace_with_signal(target=target, signal=signal, **kwargs)
                )
                for target in targets
            ]
            yield signal

    @contextlib.contextmanager
    def intercepting_modal(
        self,
        target: t.Union[t.Callable, t.Tuple[type, str]] = None,
        handler: t.Callable = None,
        timeout=0,
        wait_before=500,
        wait_after=500,
        **kwargs,
    ):
        def _default_accept_dialog(w: W.QDialog):
            self.wait_for_window_shown(w)
            _logger.info(f"About to accept dialog {w}")
            self.wait(wait_before)
            w.accept()
            self.wait(wait_after)
            _logger.info("After accepting dialog")

        target = target or (W.QDialog, "exec_")
        handler = handler or _default_accept_dialog
        signal = self._signals.callBegin

        def _modal_slot(call_info: CallInfo):
            widget = call_info.instance or call_info.args[0]
            _logger.debug(f"_modal_slot called for {widget}")

            def _to_be_called_async():
                _logger.debug(call_info)
                handler(widget, **kwargs)

            _logger.info(f"call_info.callee={call_info.callee}")
            if True:
                QtCore.QTimer.singleShot(0, _to_be_called_async)

        try:
            signal.connect(_modal_slot)
            with self.instrumenting(target) as instrumented:
                _logger.debug(f"instrumented={instrumented}")
                with self.wait_signal(signal, timeout=timeout):
                    yield
        except Exception as e:
            _logger.exception(e)
        finally:
            # must disconnect upon exiting the context or modal_slot will be connected again
            # the next time intercepting_modal() is called
            signal.disconnect(_modal_slot)

    waiting_for_modal = intercepting_modal

    @contextlib.contextmanager
    def waiting_for_dialog(self, timeout=0, dialog_cls=W.QMessageBox) -> _DialogProxy:
        signal = self._signals.dialogDisplay

        def dispatch(modal: dialog_cls):
            proxy = _DialogProxy(text=modal.text())
            print(proxy)
            signal.emit(proxy)
            return True
            # return modal.defaultButton()

        with _ModalPatcher(dialog_cls).patching(dispatch):
            with self.wait_signal(signal, timeout=timeout) as blocker:
                pass
            dialog_info_for_checking: _DialogProxy = blocker.args[0]
            yield dialog_info_for_checking

    def cleanup(self):
        self._focus_stack.clear()
