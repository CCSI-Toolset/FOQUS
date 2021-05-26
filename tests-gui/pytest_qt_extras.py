import contextlib
from dataclasses import dataclass, field
import inspect
import logging
import operator
from pathlib import Path
import shutil
import time
import typing as t

from PyQt5 import QtWidgets, QtCore, QtGui
from slugify import slugify

from pytestqt import plugin as pytestqt_plugin
from _pytest.monkeypatch import MonkeyPatch


# NOTE these values can be given to aliases used as kwargs when an actual filter is not needed
# the actual value is a matter of synctactic sugar but it should suggest the meaning of
# "any result is fine, no need to filter since I expect it to be the only one"
KWARGS_PLACEHOLDER_VALUES = {True, any, next, ..., '*', ''}


_logger = logging.getLogger('pytest_qt_extras')


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
        before: t.Callable[[CallInfo], t.Any],
        after: t.Callable[[CallInfo], t.Any]
        ) -> t.Callable[[t.Any], t.Any]:
    name = getattr(func, '__name__', None)
    instance = getattr(func, '__self__', None)
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
        before(info)
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            info.exception = e
            raise e from None
        else:
            info.result = res
        finally:
            after(info)

    return _wrapped


@contextlib.contextmanager
def instrument(target, signal_before=None, signal_after=None):
    mp = MonkeyPatch()

    _logger.info(f'instrumenting target {target}')
    if isinstance(target, tuple) and len(target) == 2:
        owner, name = target
        instance = None
    # TODO check if methodtype?
    else:
        instance = getattr(target, '__self__', None)
        owner = instance.__class__
        name = target.__name__
    func = getattr(owner, name)
    assert callable(func), f'{func} must be callable'

    _logger.debug(f'target={target}')
    _logger.debug(f'name={name}')
    _logger.debug(f'owner={owner}')
    _logger.debug(f'func={func}')

    def _do_nothing(*args, **kwargs): ...

    _patched_callable = _wrap_callable(
        func,
        before=signal_before.emit if signal_before else _do_nothing,
        after=signal_after.emit if signal_after else _do_nothing
    )

    mp.setattr(owner, name, _patched_callable)
    patched_info = _WrappedCallable(
        wrapped=func,
        name=name,
        instance=instance,
        wrapper=_patched_callable,
    )
    _logger.info('returning patched object')
    yield patched_info
    _logger.info('start undoing monkeypatching')
    mp.undo()
    _logger.info('monkeypatching done')



def _get_sibling_label_text(widget):
    preceding_siblings = []
    _logger.debug(f'searching label for {widget}')

    def get_order_key_top_down_left_right(w):
        top_left = w.geometry().topLeft()
        return (top_left.y(), top_left.x())

    search_pool = [
        w
        for w in widget.parent().findChildren(QtWidgets.QWidget)
        if (isinstance(w, QtWidgets.QLabel) or w is widget)
    ]
    ordered_as_text = sorted(search_pool, key=get_order_key_top_down_left_right)

    for child in ordered_as_text:
        if child == widget:
            break
        if child.isVisible():
            _logger.debug(f'Adding {child} (text={child.text()})')
            preceding_siblings.append(child)
        else:
            _logger.debug(f'Widget not visible: {child} (text={child.text()}')

    # reversed to search for the label from closest to farthest
    for sibling in reversed(preceding_siblings):
        if isinstance(sibling, QtWidgets.QLabel):
            label = sibling
            _logger.debug(f'\tlabel.text()={label.text()}')
            return label.text()


@dataclass(frozen=True)
class TextHintFilter:
    hint: str
    get_queryable_text: t.Callable[[QtWidgets.QWidget], str] = str
    compare: t.Callable[[str, str], bool] = str.__eq__
    transform: t.Callable[[str], str] = str
    # these are mostly here for reference since they're mainly used to build compare() and transform()
    case_sensitive: bool = None
    truncation_symbol: str = None

    @classmethod
    def build(cls, hint: str, case_sensitive: t.Union[str, bool] = 'smart', truncation_symbol: str = '[...]', **kwargs):
        if case_sensitive == 'smart':
            case_sensitive = hint.casefold() != hint

        transform = str if case_sensitive else str.casefold
        compare = cls._get_compare_func(hint, truncation_symbol)

        return cls(
            hint=hint,
            transform=transform,
            compare=compare,
            case_sensitive=case_sensitive,
            truncation_symbol=truncation_symbol,
            **kwargs
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

    def __call__(self, widget=None, text: str = None):
        str_to_search_for = self.hint.replace(self.truncation_symbol, '')
        if widget is None and text is not None:
            str_to_search_in = text
        elif widget is not None and text is None:
            str_to_search_in = self.get_queryable_text(widget)
        else:
            raise ValueError
        if str_to_search_in is None:
            is_match = False
        else:
            is_match = self.compare(
                self.transform(str_to_search_in),
                self.transform(str_to_search_for)
            )
        info = dict(
            text=str_to_search_in,
        )

        return is_match, info


class FilterOutcome:
    "Outcome of applying a single filter to a single candidate"
    # TODO should it hold a reference to the candidate?
    # i'd say that it either has both the candidate and the filter, or neither of them
    def __init__(self, is_match: bool = None, error=None, **kwargs):
        self._is_match = bool(is_match)
        self.error = error
        self.info = kwargs

    @property
    def is_match(self):
        return self._is_match and not self.error

    def __bool__(self):
        return self.is_match

    def __repr__(self):
        return f'{self.__class__.__name__}({self.is_match}, {self.info})'


# if we define "Handler" as anything that wraps and acts on a single widget object,
# this could be a SearchHandler and the Agent an ActionHandler
class SearchHandler:
    def __init__(self, candidate):
        self._candidate = candidate
        self._outcomes = {}

    @property
    def candidate(self):
        return self._candidate

    @property
    def outcomes(self):
        return self._outcomes.values()

    def __iter__(self):
        yield from self.outcomes

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.candidate})>'

    @property
    def is_match(self):
        return all(self.outcomes)

    @property
    def is_partial_match(self):
        return any(self.outcomes)

    def matches_filter(self, filter_):
        return bool(self._outcomes[filter_])

    @property
    def info(self):
        return {
            f: dict(outcome.info)
            for f, outcome in self._outcomes.items()
        }

    def summarize(self):
        for f, outcome in self._outcomes.items():
            print(f'filter={f}')
            print(f'is_match={outcome.is_match}')
            for k, v in outcome.info.items():
                print(f'\t{k}: {v}')

    def apply(self, filter_):
        try:
            result = filter_(self.candidate)
        except Exception as e:
            _logger.warning(f'exception: {e}')
            to_store = FilterOutcome(is_match=None, error=e)
        else:
            if isinstance(result, tuple):
                is_match, info = result
            else:
                is_match, info = result, {}
            to_store = FilterOutcome(is_match, **info)
        finally:
            self._outcomes[filter_] = to_store
        return to_store


class SearchMatches:
    def __init__(self, items=None):
        self._all_items = list(items or [])
        self._handlers = [SearchHandler(item) for item in self._all_items]

    def __iter__(self):
        yield from self._handlers

    def apply_filter(self, filter_):
        _logger.debug(f'applying filter {filter_}')
        for handler in self:
            outcome = handler.apply(filter_)
            _logger.debug(f'\t\t{handler}:\t{outcome}')

    def apply_filters(self, filters):
        for f in filters:
            self.apply_filter(f)

    @property
    def matching_items(self):
        return [_.candidate for _ in self if _.is_match]

    def __len__(self):
        return len(self.matching_items)

    @property
    def has_matches(self):
        return len(self) > 0

    @property
    def has_unique_match(self):
        return len(self) == 1

    def describe(self):
        for handler in self:
            print(f'-----------------{handler}[{handler.is_match}]')
            handler.summarize()

    def __getitem__(self, key):
        if self.has_unique_match:
            return self.matching_items[0]
        if not self.has_matches:
            self.describe()
            raise NotEnoughMatchesError()
        if key is None:
            self.describe()
            raise TooManyMatchesError(f"There are {len(self)} matching items, but key={key} was provided")
        return self.matching_items[key]


def get_active_windows():
    app = QtWidgets.QApplication.instance()
    return [
        w for w in app.topLevelWidgets()
        if w.isWindow()
        and w.isVisible()
    ]


class Highlighter(QtWidgets.QRubberBand):

    @classmethod
    def create(cls, widget, **kwargs):
        hl = cls(QtWidgets.QRubberBand.Rectangle, parent=widget, **kwargs)
        geom = widget.rect()
        hl.setGeometry(geom)
        return hl

    def __init__(self, *args, color=QtCore.Qt.gray, text: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = color
        self.text = text
        # self.setStyle(QtWidgets.QStyleFactory.create('windowsvista'))

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, *args):
        self.hide()

    def paintEvent(self, ev):
        painter = QtGui.QPainter()
        painter.begin(self)
        # painter.setBrush(QtGui.QColor(255, 0, 0))
        # pen = QtGui.QPen(QtCore.Qt.green, 1, QtCore.Qt.SolidLine)
        # painter.setPen(pen)
        # painter.fillRect(w.rect(), QtGui.QColor(255, 0, 0))
        hw = 2
        base = self.geometry()
        outer = QtCore.QRect(base.topLeft().x() - hw, base.topLeft().y() - hw, base.width() + hw, base.height() + hw)
        painter.setPen(QtGui.QPen(self.color, 2 * hw, QtCore.Qt.SolidLine))
        painter.drawRect(base)
        if self.text:
            painter.drawText(base, 0, self.text)
        painter.end()


class TreePath:
    def __init__(self, items):
        self._items = list(items or [])

    def with_appended(self, item):
        return type(self)(self._items + [item])

    def __iter__(self):
        return iter(self._items)

    def __str__(self):
        return _join(self, sep='.')


@dataclass
class WidgetInfo:
    widget: QtWidgets.QWidget
    tree_path: TreePath
    geometry: t.Any = None
    n_children: int = None

    @classmethod
    def collect(cls, w, tree_path=None):
        tree_path = tree_path or TreePath([0])
        children = w.children()
        info = cls(
            widget=w,
            tree_path=tree_path,
            geometry=w.geometry(),
            n_children=len(children),
        )
        yield info
        for idx, child in enumerate(children):
            if isinstance(child, QtWidgets.QWidget):
                yield from cls.collect(
                    child,
                    tree_path.with_appended(idx)
                )

    def __str__(self):
        s = f'{self.tree_path}'
        s += f'\n\t{self.widget}'
        s += f'\n\tgeometry={self.geometry}'
        if self.n_children:
            s += f'\n\tn_children={self.n_children}'
        return s


class HierarchyInfo:
    def __init__(self, root: QtWidgets.QWidget):
        self._root = root
        self._items = None
        self._annotations = []

    def __iter__(self) -> t.Iterable[WidgetInfo]:
        if self._items is None:
            self._items = [
                info for info in WidgetInfo.collect(self._root)
                if info.widget.isVisible()
                and not type(info.widget) in {QtWidgets.QWidget, Highlighter}
            ]    
        return iter(self._items)

    def __str__(self):
        lines = [str(info) for info in self]
        return str.join('\n', lines)

    @contextlib.contextmanager
    def highlighting(self):
        try:
            for widget_info in self:
                hl = Highlighter.create(
                    widget_info.widget,
                    text=_join(widget_info.tree_path, sep='.')
                )
                hl.color = QtCore.Qt.darkRed
                self._annotations.append(hl)
                hl.show()
            yield self._annotations
        except Exception as e:
            _logger.exception(e)
        finally:
            for obj in self._annotations:
                obj.deleteLater()


class Agent:
    def __init__(self, target: QtWidgets.QWidget, dispatcher=None, target_identifier=None):
        self._target = target
        self._dispatcher = dispatcher
        self._target_identifier = target_identifier or (type(self.target).__name__,)
        self._highlighter = None

    def __repr__(self):
        return f'<{self.__class__.__name__}(target={self.target} as="{self.readable_target}")>'

    @property
    def target(self):
        return self._target

    @property
    def target_identifier(self):
        return self._target_identifier

    @property
    def readable_target(self):
        return _join(reversed(self.target_identifier))

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def highlighter(self):
        if self._highlighter is None:
            self._highlighter = Highlighter.create(self.target)
        return self._highlighter

    @contextlib.contextmanager
    def highlighting(self, color=None):
        hl = self.highlighter
        if color:
            hl.color = color
        hl.show()
        yield hl
        hl.hide()

    @contextlib.contextmanager
    def highlighting_children(self):
        to_highlight = [
            w for w in self.target.findChildren(QtWidgets.QWidget)
            if (w.isVisible() and not type(w) in {QtWidgets.QWidget, Highlighter})
        ]
        annotations = []
        try:
            for idx, child in enumerate(to_highlight):
                hl = Highlighter.create(child, text=str(idx))
                annotations.append(hl)
                hl.color = QtCore.Qt.red
                print(f'{idx:2d}: {child}')
                print(f'\tgeometry={child.geometry()}')
                parent = child.parent()
                layout = child.layout() or parent.layout()
                print(f'\tparent={child.parent()}')
                print(f'\tlayout={layout}')
                if layout:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        item_content = item.widget() or item.layout()
                        print(f'\t\t{i}: {item_content}')
                    print(f'\t{layout.indexOf(child)}')
                print(f'\ttext={getattr(child, "text", lambda: None)()}')
                hl.show()
            yield
        except Exception as e:
            _logger.exception(e)
        finally: 
            for obj in annotations:
                obj.deleteLater()

    @classmethod
    def get_queryable_text(cls, w):
        return _get_sibling_label_text(w)

    @classmethod
    def get_queryable_data(cls, w: QtWidgets.QWidget, text=None, text_field=None, **kwargs):
        def get_object_id(obj):
            return str(hex(id(obj)))
        parent = w.parent()
        d = dict(
            type=type(w),
            id=get_object_id(w),
            parent_type=type(parent),
            parent_id=get_object_id(parent),
            is_visible=w.isVisible(),
            is_enabled=w.isEnabled(),
            text=text,
            text_field=text_field,
            **kwargs
        )
        return d

    def do(self, action_name: str, *args, **kwargs):
        action_func = getattr(self, action_name)
        if action_func is None:
            raise NotEnoughMatchesError(agent=self, action_name=action_name)
        return action_func(*args, **kwargs)

    def __eq__(self, other):
        return type(self) == type(other) and self.target == other.target

    @classmethod
    def is_visible(cls, w: QtWidgets.QWidget) -> t.Tuple[bool, dict]:
        def get_object_id(obj):
            return str(hex(id(obj)))

        parent = w.parent()
        xy = w.rect().topLeft().x(), w.rect().topLeft().y()
        info = dict(
            type=type(w),
            id=get_object_id(w),
            parent_type=type(parent),
            parent_id=get_object_id(parent),
            geometry=w.geometry()
        )
        is_visible = w.isVisible()

        return is_visible, info

    @classmethod
    def is_enabled(cls, w: QtWidgets.QWidget) -> bool:
        return w.isEnabled()

    def locate(
            self,
            target=None,
            hint=None,
            case_sensitive=None,
            index=None,
            require_visible=True,
            require_enabled=False,
            **kwargs
        ) -> QtWidgets.QWidget:
        # TODO the logic to translate the params to lower-level search args is done here
        # e.g. button="Foo" -> search(QtWidgets.QAbstractButton, name="Foo")
        if isinstance(target, QtWidgets.QWidget):
            return target
        if target is not None and issubclass(target, QtWidgets.QWidget):
            widget_cls = target
        else:
            widget_cls, alias = self.dispatcher.resolve_alias(kwargs)
            hint_from_alias = kwargs.pop(alias)
            if hint_from_alias is not None:
                if hint is None:
                    hint = hint_from_alias
                else:
                    raise ValueError(f'Ambiguous specification: both hint={hint} and {alias}={hint_from_alias} were provided')

        agent_cls = self.dispatcher.get(widget_cls)

        if hint in KWARGS_PLACEHOLDER_VALUES:
            filter_ = None
        elif hint is None or callable(hint):
            filter_ = hint
        elif isinstance(hint, str):
            filter_ = TextHintFilter.build(
                hint=hint,
                case_sensitive=case_sensitive,
                get_queryable_text=agent_cls.get_queryable_text
            )
        else:
            raise ValueError(f'If "hint" is used, it should be a callable or a string, but an object of type {type(hint)} was provided')

        _logger.info(f'locating widget within search root {self.target}')
        cands = self.target.findChildren(widget_cls)
        all_children = self.target.findChildren(QtWidgets.QWidget)
        # print(f'all_children={all_children}')
        filters = []
        if require_visible:
            filters.append(agent_cls.is_visible)
        if require_enabled:
            filters.append(agent_cls.is_enabled)
        if filter_:
            filters.append(filter_)

        _logger.info(f'filters={filters}')
        matches = SearchMatches(cands)
        matches.apply_filters(filters)
        result = matches[index]
        _logger.info(f'result={result}')
        return result


class InvalidMatchError(ValueError):
    def __init__(self, *args, explain: t.Callable = (lambda: None), **kwargs):
        super().__init__(*args, **kwargs)
        self.explain = explain

    def __str__(self):
        self.explain()
        return super().__str__()


class NotEnoughMatchesError(InvalidMatchError):
    pass


class TooManyMatchesError(InvalidMatchError):
    pass


def _join(it, sep=' '):
    def is_to_skip(s):
        return any(s == to_skip for to_skip in ['', None])
    return str.join(sep, [str(_) for _ in it if not is_to_skip(_)])


@dataclass
class Action:
    name: str
    agent: Agent
    args: tuple = None
    prose_template: str = None

    @property
    def target(self):
        return self.agent.readable_target

    @property
    def description(self):

        if not self.args:
            return f'{self.name.title()} the {self.target}.'
        return f'Using the {self.target}, {self.name} {_join(self.args)}.'


class _Signals(QtCore.QObject):
    __instance = None
    beforeCall = QtCore.pyqtSignal(CallInfo)
    afterCall = QtCore.pyqtSignal(CallInfo)
    actionStarted = QtCore.pyqtSignal(Action)
    actionEnded = QtCore.pyqtSignal(Action)
    locateStarted = QtCore.pyqtSignal(object)
    locateEnded = QtCore.pyqtSignal(object)

    @classmethod
    def instance(cls) -> '_Signals':
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance


def action(f):
    signals = _Signals.instance()
    name = f.__name__
    def _wrapped(*args, **kwargs):
        agent = args[0]
        action = Action(name=name, agent=agent, args=args[1:])
        signals.actionStarted.emit(action)
        f(*args, **kwargs)
        signals.actionEnded.emit(action)
    ...
    return _wrapped


class Dispatcher:
    def __init__(self):
        self._dispatch_map: t.Dict[type, t.Callable[[t.Any], Agent]] = {object: Agent}
        self._alias_map: t.Dict[str, type] = {}

    def register(self, widget_cls, agent_cls=None, aliases=None):
        if agent_cls is not None:
            self._dispatch_map[widget_cls] = agent_cls
        if aliases is not None:
            for alias in aliases:
                self._alias_map[alias] = widget_cls

    def __contains__(self, obj):
        return obj in self._dispatch_map

    @property
    def dispatch_rules(self):
        items = list(self._dispatch_map.items())
        return reversed(items)

    def get(self, target):
        matcher = issubclass if isinstance(target, type) else isinstance
        for match_key, match_val in self.dispatch_rules:
            if matcher(target, match_key):
                _logger.debug(f'found match between {match_key} and {target}: {match_val}')
                return match_val
        raise ValueError(f"No matching value found for {target}")

    def _get_identifier_info(self, *args, **kwargs):
        def to_token(obj):
            if isinstance(obj, type):
                return obj.__name__
            if isinstance(obj, QtWidgets.QWidget):
                return obj.__class__.__name__
            if obj in KWARGS_PLACEHOLDER_VALUES:
                return ''
            return str(obj)
        all_extra_params = []
        all_extra_params.extend(args)
        for kv in kwargs.items():
            all_extra_params.extend(kv)
        return [to_token(p) for p in all_extra_params]

    def get_agent(self, target, *args, **kwargs) -> Agent:
        agent_cls = self.get(target)
        id_info = self._get_identifier_info(*args, **kwargs)
        return agent_cls(target, dispatcher=self, target_identifier=id_info)

    def __call__(self, **kwargs) -> Agent:
        return self.get_agent(**kwargs)


class WidgetDispatcher(Dispatcher):

    def resolve_alias(self, kwargs: dict):
        alias_map = self._alias_map

        alias_in_kwargs: t.Set = kwargs.keys() & alias_map.keys()
        n_matching_kwargs = len(alias_in_kwargs)
        if n_matching_kwargs == 0:
            raise NotEnoughMatchesError(expected=1, found=0, kwargs=kwargs, aliases=list(alias_map.keys()))
        elif n_matching_kwargs > 1:
            raise TooManyMatchesError(expected=1, found=list(alias_in_kwargs))
        alias = alias_in_kwargs.pop()
        widget_cls = alias_map[alias]

        return widget_cls, alias

    def _make_get_queryable_text(self, widget_cls):
        agent_cls = self.get(widget_cls)
        return agent_cls.get_queryable_text


TableRowSpec = t.Union[int, str, None]
TableColumnSpec = t.Union[int, str]


class TableAgent(Agent):

    @property
    def table(self) -> QtWidgets.QTableWidget:
        return self.target

    @action
    def select_row(self, row: TableRowSpec):
        row_idx = self._get_row_idx(row)
        self.table.selectRow(row_idx)
        _logger.debug(f'self.table.currentRow()={self.table.currentRow()}')
        _logger.debug(f'self.table.currentColumn()={self.table.currentColumn()}')

    @action
    def select_cell(self, row: TableRowSpec, col: TableColumnSpec):
        row_idx = self._get_row_idx(row)
        col_idx = self._get_col_idx(col)
        self.table.setCurrentCell(row_idx, col_idx)

    @action
    def select(self, row: TableRowSpec = None, col: TableColumnSpec = 0):
        self.select_cell(row, col)

    def _get_row_idx(self, row: TableRowSpec = None):
        if isinstance(row, int):
            return row
        if row is None:
            if self.table.rowCount() == 1:
                row_idx = 0
            else:
                # TODO what does currentRow() return if no row is selected?
                # maybe the safest thing to do is to raise an exception prompting to select a row first
                row_idx = self.table.currentRow()
        return row_idx

    def _find_column_by_name(self, column_name: str, table):
        for col_idx in range(table.columnCount()):
            header_text = table.horizontalHeaderItem(col_idx).text()
            _logger.debug(f'column_name={column_name}')
            _logger.debug(f'header_text={header_text}')
            if column_name == header_text:
                _logger.debug(f'found: {column_name} -> {col_idx}')
                return col_idx

    def _get_col_idx(self, col: TableColumnSpec = None):
        if isinstance(col, int):
            return col
        if isinstance(col, str):
            return self._find_column_by_name(col, self.table)
        if col is None:
            if self.table.columnCount() == 1:
                col_idx = 0
        return col_idx

    def _get_cell_content(
            self,
            row: TableRowSpec,
            col: TableColumnSpec,
        ):
        row_idx = self._get_row_idx(row)
        col_idx = self._get_col_idx(col)
        _logger.debug(f'col, row={row_idx, col_idx}')

        widget = self.table.cellWidget(row_idx, col_idx)
        _logger.debug(f'widget={widget}')
        item = self.table.item()
        _logger.debug(f'item={item}')
        if widget is None:
            widget = item
        return widget

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
            self,
            row: TableRowSpec = None,
            column: TableColumnSpec = None,
            **kwargs
        ):
        "Locate a widget within (i.e. in a cell of) the table."
        if column is None and len(kwargs) == 1:
            column = set(kwargs.values()).pop()
        row_idx = self._get_row_idx(row)
        col_idx = self._get_col_idx(column)
        _logger.debug(f'col, row={row_idx, col_idx}')
        widget = self.table.cellWidget(row_idx, col_idx)
        if widget is None:
            widget = item = self.table.item(row, col_idx)
        _logger.debug(f'get_table_cell_content::widget={widget}')
        return widget


class ButtonAgent(Agent):
    @classmethod
    def get_queryable_text(cls, w: QtWidgets.QAbstractButton):
        return w.text().replace('&', '')

    @action
    def click(self):
        self.target.click()


class ComboBoxAgent(Agent):
    @property
    def items(self):
        return [
            self.target.itemText(i)
            for i in range(self.target.count())
        ]

    def display_items(self):
        print(f'contents of {self.target}:')
        for i, text in enumerate(self.items):
            print(f'\t{i}: {text}')

    @action
    def set_option(self, text, **kwargs):
        matching_idx = self.target.findText(text)
        if matching_idx == -1:
            raise NotEnoughMatchesError(f'No matches found for "{text}"', explain=self.display_items)
        self.target.setCurrentIndex(matching_idx)


class ListWidgetAgent(Agent):

    # @action(prose='set the "{0}" option')
    @action
    def set_option(self, text, **kwargs):
        matches = self.target.findItems(text, QtCore.Qt.MatchExactly)
        n_matches = len(matches)
        assert n_matches == 1, f'Expected exactly 1 match, found {n_matches} instead: {matches}'
        self.target.setCurrentItem(matches[0])


class InputAgent(Agent):

    @action
    def enter_value(self, value):
        try:
            self.target.setValue(value)
        except AttributeError:
            self.target.setText(str(value))


class RadioButtonAgent(ButtonAgent):
    @action
    def select(self):
        self.target.click()


class TabsAgent(Agent):
    @property
    def tabs(self) -> QtWidgets.QTabWidget:
        return self.target

    @action
    def set_visible(self, text):
        for tab_idx in range(self.tabs.count()):
            tab_text = self.tabs.tabText(tab_idx)
            if text in tab_text:
                self.tabs.setCurrentIndex(tab_idx)
                return tab_idx


class GroupBoxAgent(Agent):
    @classmethod
    def get_queryable_text(cls, w: QtWidgets.QGroupBox):
        return w.title()


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

    def add(self, item: _TestArtifact):
        self._items.append(item)
        if not self.save_later:
            self.save(item)

    def save(self, item: _TestArtifact):
        item_dir = Path(self.base_path)
        progressive_id = len(self)
        filename = slugify(f'{progressive_id}-{item.label}')
        item_path = item_dir / filename
        try:
            return item.save(item_path)
        except Exception as e:
            _logger.error(f'Error while saving artifact at {item_path}')
            _logger.exception(e)
        else:
            _logger.info(f'Saved artifact at {item_path}')

    def save_all(self):
        for item in self:
            self.save_item(item)



class Snapshot(_TestArtifact):

    @classmethod
    def take(cls, native_widget: QtWidgets.QWidget = None, **kwargs):
        native_widget = native_widget or QtWidgets.QApplication.instance().activeWindow()
        try:
            win_handle = native_widget.windowHandle()
            screen = win_handle.screen()
            pixmap = screen.grabWindow(win_handle.winId())
        except Exception as e:
            _logger.error(f'Could not capture pixmap ({kwargs})')
            _logger.exception(e)
            pixmap = None
        return cls(
            pixmap=pixmap,
            **kwargs
        )

    @classmethod
    def from_widget(cls, widget: QtWidgets.QWidget, entire_window=True, **kwargs):
        to_grab = widget.window() if entire_window else widget
        pixmap = to_grab.grab()
        return cls(
            pixmap=pixmap,
            **kwargs
        )

    def __init__(self, pixmap: QtGui.QPixmap = None, text: str = None, **kwargs):
        super().__init__(**kwargs)
        self._pixmap = pixmap
        self.text = text

    def save(self, path: Path):
        if self._pixmap is None:
            _logger.warning(f'No pixmap to save for {self}')
        else:
            self._pixmap.save(path.with_suffix('.png').__fspath__())
        if self.text:
            path.with_suffix('.txt').write_text(self.text)



class QtBot(pytestqt_plugin.QtBot):
    "Extends original class with a few convenience methods"

    def __init__(
            self,
            *args,
            focused: QtWidgets.QWidget = None,
            slowdown_wait=500,
            artifacts_path='.pytest-artifacts',
            **kwargs
        ):
        super().__init__(*args, **kwargs)

        self._focus_stack = []
        self._dispatcher = None

        self.focused = focused or QtWidgets.QApplication.instance().activeWindow()

        self._descriptions = []
        self._artifacts_base_path = Path(artifacts_path)
        self._screenshots = ArtifactManager(self._artifacts_base_path / 'screenshots')
        self._snapshots = ArtifactManager(self._artifacts_base_path / 'snapshots')

        self._signals = _Signals.instance()
        self._init_signals()

        self._slowdown_wait = slowdown_wait

    def _init_signals(self):
        self._signals.actionStarted.connect(lambda a: _logger.info(f'Action started: {a}'))
        self._signals.actionEnded.connect(lambda a: _logger.info(f'Action ended: {a}'))
        self._signals.actionEnded.connect(self.add_description)
        self._signals.actionStarted.connect(self.start_highlight)
        self._signals.actionEnded.connect(self.stop_highlight)

    def add_description(self, action):
        self._descriptions.append(action.description)

    def take_screenshot(self, label):
        # TODO add metadata on the test where the screenshot originates from
        shot = Snapshot.from_widget(self.focused, label=label)
        self._screenshots.add(shot)

    @contextlib.contextmanager
    def taking_screenshots(self, actions=True):
        take_scr = self.take_screenshot

        def take_scr(action, when):
            widget = action.agent.target
            for_window = Snapshot.from_widget(widget=widget, label=f'{when}-{action.description}')
            for_widget = Snapshot.from_widget(widget=widget, entire_window=False, label=f'{when}-{action.description}-widget-only')
            self._screenshots.add(for_window)

        take_before = lambda a: take_scr(a, 'before')
        take_after = lambda a: take_scr(a, 'after')

        sig = self._signals
        sig.actionStarted.connect(take_before)
        sig.actionEnded.connect(take_after)

        try:
            yield take_scr
        finally:
            sig.actionStarted.disconnect(take_before)
            sig.actionEnded.disconnect(take_after)

    def describe(self):
        for line in self._descriptions:
            print(line)

    def slow_down(self):
        self.wait(self._slowdown_wait)

    def start_highlight(self, action):
        hl = action.agent.highlighter
        hl.color = QtCore.Qt.red
        hl.show()
        self.slow_down()

    def stop_highlight(self, action):
        self.slow_down()
        action.agent.highlighter.hide()

    def take_widget_snapshot(self):
        root = self.focused
        info = HierarchyInfo(root)
        with info.highlighting():
            self.slow_down()
            snapshot = Snapshot.from_widget(
                widget=root,
                label=str(root),
            )
            snapshot.text = str(info)
        self.slow_down()
        self._snapshots.add(snapshot)

    def _create_dispatcher(self):

        dispatcher = WidgetDispatcher()
        r = dispatcher.register

        r(QtWidgets.QPushButton, agent_cls=ButtonAgent, aliases=['button'])
        r(QtWidgets.QRadioButton, agent_cls=RadioButtonAgent, aliases=['radio_button'])
        r(QtWidgets.QComboBox, agent_cls=ComboBoxAgent, aliases=['combo_box'])
        r(QtWidgets.QListView, agent_cls=ListWidgetAgent, aliases=['item_list'])
        r(QtWidgets.QSpinBox, agent_cls=InputAgent, aliases=['spin_box'])
        r(QtWidgets.QTextEdit, agent_cls=InputAgent, aliases=['text_edit_area'])
        r(QtWidgets.QLineEdit, agent_cls=InputAgent, aliases=['line_edit_area'])
        r(QtWidgets.QGroupBox, agent_cls=GroupBoxAgent, aliases=['group_box'])
        r(QtWidgets.QTabWidget, agent_cls=TabsAgent)
        r(QtWidgets.QTableWidget, agent_cls=TableAgent, aliases=['table'])

        return dispatcher

    @property
    def dispatcher(self) -> WidgetDispatcher:
        if self._dispatcher is None:
            self._dispatcher = self._create_dispatcher()
        return self._dispatcher

    @property
    def focused(self) -> QtWidgets.QWidget:
        return self._focus_stack[-1]

    @focused.setter
    def focused(self, new: QtWidgets.QWidget):
        self._focus_stack.append(new)

    @focused.deleter
    def focused(self):
        self._focus_stack.pop(-1)

    @property
    def agent(self):
        return self.dispatcher.get_agent(self.focused)

    def locate(self, target=None, hint=None, **kwargs):
        if isinstance(target, QtWidgets.QWidget):
            return target
        self.take_widget_snapshot()
        locate_spec = dict(target=target, hint=hint, kwargs=kwargs)
        with self.agent.highlighting(color=QtCore.Qt.blue):
            self.take_screenshot(f'locate-{locate_spec}')
            self.slow_down()
            try:
                _logger.info(f'qtbot.locate({locate_spec}')
                res = self.agent.locate(target=target, hint=hint, **kwargs)
            except InvalidMatchError as e:
                _logger.error(f'invalid match for QtBot.locate({locate_spec})')
                self.take_screenshot(f'invalid-match-{e}-{locate_spec}')
                raise e
        return res

    @contextlib.contextmanager
    def switching_focused(self, *args, **kwargs):
        new = self.locate(*args, **kwargs)
        self.focused = new
        try:
            yield new
        finally:
            del self.focused
    focusing_on = searching_within = switching_focused

    def get_agent(self, *args, **kwargs):
        # without arguments, just return its own agent (i.e. the agent that refers to the currently focused widget)
        if not (args or kwargs):
            return self.agent
        target = self.locate(*args, **kwargs)
        return self.dispatcher.get_agent(target, *args, **kwargs)
    using = get_agent

    def click(self, *args, **kwargs):
        return self.get_agent(*args, **kwargs).click()

    def set_option(self, value, *args, **kwargs):
        return self.get_agent(*args, **kwargs).set_option(value)

    def enter_value(self, value, *args, **kwargs):
        return self.get_agent(*args, **kwargs).enter_value(value)

    def select(self, *args, **kwargs):
        return self.get_agent(*args, **kwargs).select()

    def select_row(self, row, *args, **kwargs):
        return self.get_agent(*args, **kwargs).select_row(row)

    def show_tab(self, tab_name):
        return self.get_agent(QtWidgets.QTabWidget).set_visible(tab_name)

    def wait_until_called(self, func, before=False, **kwargs):
        signal_before = self._signals.beforeCall
        signal_after = self._signals.afterCall
        signal_to_wait_for = signal_before if before else signal_after

        with instrument(func, signal_before=signal_before, signal_after=signal_after) as instrumented:
            self.wait_signal(signal_to_wait_for, check_params_cb=instrumented.matches_call, **kwargs)

    @contextlib.contextmanager
    def intercept_modal(self, target: t.Union[t.Callable, t.Tuple[type, str]] = None, handler: t.Callable = None, timeout=0, wait_before=500, wait_after=500, **kwargs):
        def _accept_dialog(w: QtWidgets.QDialog):
            self.wait_for_window_shown(w)
            _logger.info(f'About to accept dialog {w}')
            self.wait(wait_before)
            w.accept()
            self.wait(wait_after)
            _logger.info('After accepting dialog')

        target = target or (QtWidgets.QDialog, 'exec_')
        handler = handler or _accept_dialog

        signal = self._signals.beforeCall

        def _modal_slot(call_info: CallInfo):
            widget = call_info.instance or call_info.args[0]
            _logger.debug(f'_modal_slot called for {widget}')
            def _to_be_called_async():
                _logger.debug(call_info)
                handler(widget, **kwargs)
            _logger.info(f'call_info.callee={call_info.callee}')
            if True:
                QtCore.QTimer.singleShot(0, _to_be_called_async)

        signal.connect(_modal_slot)

        with instrument(target, signal_before=signal) as instrumented:
            _logger.debug(f'instrumented={instrumented}')
            with self.wait_signal(signal, timeout=timeout):
                yield
        # must disconnect upon exiting the context or modal_slot will be connected again
        # the next time intercept_blocking_modal() is called
        signal.disconnect(_modal_slot)
    waiting_for_modal = intercept_modal
