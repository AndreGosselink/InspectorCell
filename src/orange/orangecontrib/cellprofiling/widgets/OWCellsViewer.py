import os

from AnyQt import QtGui, QtCore, QtWidgets
from AnyQt.QtCore import Signal, Qt, QSize, QRectF, QRect, QPointF, Slot
from AnyQt.QtGui import QColor, QPainter, QPalette, QPolygonF, QPixmap, QBrush, QImage, QPen, QIcon, QTransform, QFont, \
    QPainterPath
from Orange.widgets.utils.plot import OWPlotGUI, OWToolbar, StateButtonContainer
from Orange.widgets.utils.sql import check_sql_input

from Orange.widgets.visualize.utils.component import OWGraphWithAnchors

from Orange.widgets.widget import OWWidget, Input, Output, Msg, AttributeList
from Orange.widgets.settings import (
    Setting, ContextSetting, DomainContextHandler,
    SettingProvider)

from AnyQt.QtWidgets import (
    QComboBox, QGraphicsScene, QGraphicsView, QGraphicsWidget,
    QGraphicsPathItem, QGraphicsTextItem, QStyle,
    QGraphicsObject, QGraphicsItem, QSizePolicy, QGraphicsLineItem, QGraphicsPolygonItem, QFileDialog,
    QGraphicsPixmapItem)

from Orange.data import Table, Domain, DiscreteVariable, Variable, ContinuousVariable, FileFormat
from Orange.widgets.io import MatplotlibFormat, MatplotlibPDFFormat
from Orange.widgets import gui
from Orange.widgets.utils import colorpalette, colorbrewer, saveplot, getdeepattr
from Orange.widgets.utils.itemmodels import DomainModel
from Orange.statistics.util import bincount
from Orange.widgets.utils.colorpalette import (
    ColorPaletteGenerator, ContinuousPaletteGenerator, DefaultRGBColors
)

from Orange.widgets.utils.widgetpreview import WidgetPreview

from Orange.widgets.visualize.owscatterplotgraph import DiscretizedScale, LegendItem, PaletteItemSample

from collections import namedtuple
import numpy as np
import pyqtgraph as pg

MAX_CATEGORIES = 15  # maximum number of colors or shapes (including Other)
DarkerValue = 120
UnknownColor = (168, 50, 168)

COLOR_NOT_SUBSET = (128, 128, 128, 0)
COLOR_SUBSET = (128, 128, 128, 255)
COLOR_DEFAULT = (128, 128, 128, 0)
MAX_VISIBLE_LABELS = 500

BgImgFormats = [
    "Tiff file (*.tif)",
    "Jpg file (*.jpg *jpeg)",
    "Png file (*.png)",
]


class CellsViewerLegend(QGraphicsItem):
    def __init__(self, items, pos_x, pos_y, parent, **kwargs):
        super().__init__(None, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.items = items
        self.n_items = 0 if self.items is None else len(self.items)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.parent = parent

    def paint(self, painter, option, widget):
        painter.setOpacity(0.9)
        painter.setBrush(QtGui.QBrush(QColor(221, 221, 221, 150)))

        painter.drawRect(self.pos_x - 85, self.pos_y - 24 * self.n_items - 30, 80, 24 * self.n_items + 25)

        for i, label in enumerate(self.items):
            color = QColor(*self.parent.palette.getRGB(i))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(self.pos_x - 85 + 15, self.pos_y - 24 * self.n_items - 5 + 22 * i), 8, 8)
            painter.setPen(QColor(0, 0, 0, 255))
            painter.drawText(QPointF(self.pos_x - 85 + 30, self.pos_y - 24 * self.n_items + 22 * i), str(label))

    def boundingRect(self):
        return QRectF(self.pos_x - 85, self.pos_y - 24 * self.n_items - 30, 80, 24 * self.n_items + 25)


class CellViewerScene(QGraphicsScene):
    def __init__(self, *args, **kwds):
        QGraphicsScene.__init__(self, *args, **kwds)

    def mousePressEvent(self, event):
        itemUnderMouse = self.itemAt(event.scenePos().x(), event.scenePos().y(), self.views()[0].transform())
        if itemUnderMouse is None:
            return

        if (event.modifiers() & Qt.ShiftModifier) and (itemUnderMouse.flags() & QGraphicsItem.ItemIsSelectable):
            itemUnderMouse.setSelected(not itemUnderMouse.isSelected())

        else:
            QGraphicsScene.mousePressEvent(self, event)


class Cell(QGraphicsPolygonItem):
    __shape = None

    def __init__(self, id, poly, brush, pen, **kwargs):
        super().__init__(None, **kwargs)
        self.old_pen = None
        self.id = id
        self.setBrush(brush)
        self.setPen(pen)
        self.setPolygon(poly)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self._selected = False

    def boundingRect(self):
        return self.polygon().boundingRect()

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.old_pen = self.pen()
                new_pen = QPen()
                new_pen.setColor(QColor(255, 99, 71, 255))
                new_pen.setWidth(5)
                self.setPen(new_pen)
                self._selected = True
            else:
                if self.old_pen is not None:
                    self.setPen(self.old_pen)
                    self._selected = False

        return value

    def paint(self, painter, option, widget):
        if option.state & QStyle.State_Selected:
            print("paint State_Selected", self.id)
        if option.state & QStyle.State_HasFocus:
            print("paint State_HasFocus", self.id)
        if option.state & QStyle.State_MouseOver:
            print("paint State_MouseOver", self.id)

        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawPolygon(self.polygon())


class OWCellsViewer(OWWidget):
    name = "Cells Viewer"
    icon = "icons/mywidget.svg"
    keywords = []

    class Inputs:
        data = Input("Data", Table, default=True)

    class Outputs:
        selected_data = Output("Selected Data", Table, default=True)
        data = Output("Data", Table, default=True)

    settingsHandler = DomainContextHandler()
    attr_contour = ContextSetting(None)
    attr_label = ContextSetting(None)
    attr_color = ContextSetting(None)
    selection = Setting(None, schema_only=True)
    show_legend = False
    background_image_enabled = False
    too_many_labels = Signal(bool)
    graph_name = "scene"
    autocommit = False

    class Error(OWWidget.Error):
        no_valid_contours = Msg("No contours due to no valid data.")
        no_labels_without_contours = Msg("Please select contours to get labels visible.")

    class Warning(OWWidget.Warning):
        no_display_option = Msg("No display option is selected.")

        too_many_labels = Msg(
            "Too many labels to show (zoom in or label only selected)")

    def __init__(self):
        super().__init__()
        self.data = None
        self.contours = None
        self.legend = None
        self.n_contours = 0
        self.subset_is_shown = False
        self.alpha_value = 50
        self.zoom_value = 250
        self.label_only_selection = False
        self.bg_image_filename = ""
        self.bg_image = None
        self.setup_gui()
        self.labels = []

        self._too_many_labels = False

        # self.update_legend_visibility()

    def setup_gui(self):

        layout = gui.vBox(self.controlArea, True)

        self.contour_var = DomainModel(
            placeholder="None", separators=False)

        self.label_var = DomainModel(
            placeholder="None", separators=False)

        self.color_var = DomainModel(
            placeholder="None", separators=False)

        cb_attr_contour = gui.comboBox(
            layout, self, "attr_contour", label="Contour:",
            model=self.contour_var, callback=self._on_attr_contour_changed)

        cb_attr_color = gui.comboBox(
            layout, self, "attr_color", label="Color:",
            model=self.color_var, callback=self._on_attr_color_changed)

        cb_attr_label = gui.comboBox(
            layout, self, "attr_label", label="Label:",
            model=self.label_var, callback=self._on_attr_label_changed)

        chb_label = gui.checkBox(
            layout, self, "label_only_selection", label="Label only selection",
            callback=self.update_labels)

        chb_show_legend = gui.checkBox(
            layout, self, "show_legend", label="Show legend", callback=self.update_legend_visibility)

        box_bgImg = gui.vBox(self.controlArea, True)

        chb_bgImg = gui.checkBox(
            box_bgImg, self, "background_image_enabled", label="Show background",
            callback=self._bg_image_enabled)
        icon_open_dir = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        self.btnBrowseBgImage = gui.button(box_bgImg, self, label="Fluorescent image", icon=icon_open_dir,
                                           callback=self.browse_bg_image)
        self.btnBrowseBgImage.setEnabled(False)
        self.cb_bgImg = gui.lineEdit(box_bgImg, self, "bg_image_filename")
        self.cb_bgImg.setEnabled(False)
        gui.rubber(layout)

        box_opacity = gui.vBox(self.controlArea, True)
        slider_opacity = gui.hSlider(box_opacity, self, value='alpha_value', label="Opacity: ", minValue=0,
                                     maxValue=255, step=5, callback=self._opacity_changed)
        # gui.rubber(box_opacity)

        box_zoom = gui.hBox(self.controlArea, True)
        slider_zoom = gui.hSlider(box_zoom, self, value='zoom_value', label="Zoom: ", minValue=0,
                                  maxValue=500, step=6, callback=self._zoom_changed)

        ''' 
        tb_select = gui.toolButton(box_zoom_select, self, label="", callback=self._select_button_clicked)
        tb_select.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", 'arrow.png')))
        tb_zoom_in = gui.toolButton(box_zoom_select, self, label="", callback=self._zoom_in_button_clicked)
        tb_zoom_in.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", 'zoom_in.png')))
        tb_zoom_out = gui.toolButton(box_zoom_select, self, label="", callback=self._zoom_out_button_clicked)
        tb_zoom_out.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", 'zoom_out.png')))
        tb_zoom_reset = gui.toolButton(box_zoom_select, self, label="", callback=self._zoom_reset_button_clicked)
        tb_zoom_reset.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", 'zoom_reset.png')))
        '''

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Selected", "Send Automatically",
                        box=False)

        # Main area view
        self.scene = CellViewerScene()
        # self.scene.select
        self.view = QGraphicsView(self.scene)
        self.view.setScene(self.scene)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setBackgroundRole(QPalette.Window)
        self.view.setFrameStyle(QGraphicsView.StyledPanel)

        self.mainArea.layout().addWidget(self.view)
        self.too_many_labels.connect(lambda too_many: self.Warning.too_many_labels(shown=too_many))

    @Inputs.data
    @check_sql_input
    def set_data(self, data):
        self.closeContext()
        self.data = data
        self.valid_data = None
        self.clear()
        self.check_data()

        if self.data is not None:
            self.contour_var.set_domain(self.data.domain)
            self.label_var.set_domain(self.data.domain)
            self.color_var.set_domain(self.data.domain)

            if self.data.domain is not None:
                self.attr_color = self.data.domain.class_var
            else:
                self.attr_color = None

        # self.openContext(data)
        # self.setup_plot()
        # self.commit()

    def check_data(self):
        def error(err):
            err()
            self.data = None

        self.clear_messages()
        if self.data is not None:
            print("%i instances on input\n%i features" % (
                len(self.data), len(self.data.domain.attributes)))

    def _bg_image_enabled(self):
        if self.background_image_enabled:
            self.btnBrowseBgImage.setEnabled(True)
            self.cb_bgImg.setEnabled(True)
            if self.bg_image is not None:
                self.bg_image.show()
        else:
            self.btnBrowseBgImage.setEnabled(False)
            self.cb_bgImg.setEnabled(False)
            if self.bg_image is not None:
                self.bg_image.hide()

    @Slot()
    def browse_bg_image(self):
        dlg = QFileDialog(
            self, acceptMode=QFileDialog.AcceptOpen,
            fileMode=QFileDialog.ExistingFile
        )
        filters = BgImgFormats
        dlg.setNameFilters(filters)

        if filters:
            dlg.selectNameFilter(filters[0])

        if dlg.exec_() == QFileDialog.Accepted:
            self.bg_image_filename = dlg.selectedFiles()[0]
            if self.bg_image is not None:
                print("tries to remove here")
                self.scene.removeItem(self.bg_image)
            self.bg_image = QGraphicsPixmapItem()
            self.bg_image.setPixmap(QPixmap(self.bg_image_filename))
            self.bg_image.setZValue(-100)
            self.scene.addItem(self.bg_image)

    def commit(self):
        if self.data is not None:
            ids = []
            for c in self.contours:
                if c._selected:
                    ids.append(c.id)
                    self.data[c.id]["Selected"] = True
                else:
                    self.data[c.id]["Selected"] = False
            print(ids)
            self.Outputs.selected_data.send(self.data[ids])
            self.Outputs.data.send(self.data)
        else:
            self.Outputs.selected_data.send(None)
            self.Outputs.data.send(None)

    def update_labels(self):
        self.Error.clear()

        print("update labels")

        if self.labels is not None:
            for label in self.labels:
                self.scene.removeItem(label)

        self.labels = []

        if self.get_column(self.attr_label, merge_infrequent=False) is None:
            self.Error.clear()
            return

        if self.contours is None:
            self.Error.no_labels_without_contours()
            return

        self.draw_labels()

    def draw_labels(self):

        if self.get_column(self.attr_label, merge_infrequent=False) is None:
            self.Error.clear()
            return

        if self.get_column(self.attr_contour, merge_infrequent=False) is None:
            self.Error.no_labels_without_contours()
            return

        i = 0
        for label in self.get_column(self.attr_label, merge_infrequent=False):
            text = QGraphicsTextItem()

            font = QFont()
            font.setPixelSize(10)
            text.setDefaultTextColor(QColor(249, 166, 2))
            text.setHtml(str(label))
            text.setFont(font)
            print("rect", self.contours[i].boundingRect())
            text.setPos(QPointF(self.contours[i].boundingRect().x(), self.contours[i].boundingRect().y()))


            #text.setPos(self.contours[i].boundingRect().center())
            self.labels.append(text)
            self.scene.addItem(text)
            i = i + 1

        # font = QFont()
        # font.setPixelSize(11)
        # self._signal_too_many_labels(
        #     mask is not None and mask.sum() > self.MAX_VISIBLE_LABELS)
        # if self._too_many_labels or mask is None or not np.any(mask):
        #     return

    def clear_legend(self):
        self.scene.removeItem(self.legend)
        self.legend = None

    def update_legend_visibility(self):
        if self.legend:
            self.legend.setVisible(self.show_legend and bool(self.legend.items))

    def _zoom_changed(self):
        scale_value = 2 ** ((self.zoom_value - 250) / 50)
        self.view.setTransform(QTransform().scale(scale_value, scale_value))
        self.scene.update()

    def _select_button_clicked(self):
        pass

    def _zoom_reset_button_clicked(self):
        pass

    def _opacity_changed(self):

        if self.contours is not None:
            pen_data, brush_data = self.get_colors()

            i = 0
            for contour in self.contours:
                contour.setBrush(brush_data[i])
                i = i + 1
            self.scene.update()

    def _on_attr_contour_changed(self):

        if self.data is None:
            return

        if self.contours is not None:
            for contour in self.contours:
                self.scene.removeItem(contour)

        self.clear_legend()

        self.contours = []
        self.n_contours = 0

        if self.get_column(self.attr_contour) is None:
            self.Error.clear()
            self.attr_label = None
            self._on_attr_label_changed()
            return

        if not isinstance(self.get_column(self.attr_contour)[0], str):
            self.Error.no_valid_contours()
            return

        self.n_contours = len(self.get_column(self.attr_contour))

        i = 0
        pen_data, brush_data = self.get_colors()

        for item in self.get_column(self.attr_contour):
            path = item.split(" ")
            poly = QPolygonF()
            for p in path:
                coord = p.split(",")

                if len(coord) is not 2:
                    self.Error.no_valid_contours()
                    return

                point = QtCore.QPointF(float(coord[0]), float(coord[1]))
                poly.append(point)

            # p = QGraphicsPolygonItem(poly)
            p = Cell(i, poly, brush_data[i], pen_data[i])
            self.contours.append(p)
            self.scene.addItem(p)
            i += 1

        self.Error.clear()
        cont_color = self.is_continuous_color()
        color_labels = None if cont_color else self.get_color_labels()

        if color_labels is not None:
            self.legend = CellsViewerLegend(color_labels, self.view.width(), self.view.height(), self)
            self.scene.addItem(self.legend)
            self.update_legend_visibility()

        self.scene.update()
        self.draw_labels()

    def _on_attr_label_changed(self):
        if self.data is None:
            return
        self.update_labels()

    def _on_attr_color_changed(self):
        if self.data is None:
            return
        self._on_attr_contour_changed()

    def _replot(self):
        if self.contours is not None:
            # self._setup_plot()
            pass

    def clear(self):
        self.contour_var.set_domain(None)
        self.label_var.set_domain(None)
        self.color_var.set_domain(None)

        if self.contours is not None:
            for contour in self.contours:
                self.scene.removeItem(contour)

        if self.labels is not None:
            for label in self.labels:
                self.scene.removeItem(label)

        self.attr_label = None
        self.labels = []
        self.contours = []
        self.n_contours = 0

        self.clear_legend()
        self.Error.clear()

        self.scene.update()

        # self.plot.clear()

    ''' 
    def wheelEvent(self, event):
        print("wheel event")
        print(event.angleDelta().x(), event.angleDelta().y())
        print(event.pixelDelta().x(), event.pixelDelta().y())
        if event.angleDelta().x() > 0:
            self.zoom += 1.25
        else:
            self.zoom += 0.8

        self.view.scale(self.zoom, self.zoom)
    '''

    def setup_plot(self):
        if self.contours is None:
            return
        myPen = QPen(Qt.green, 2)
        for c in self.contours:
            self.scene.addPolygon(c, myPen)

    def is_continuous_color(self):
        return self.attr_color is not None and self.attr_color.is_continuous

    def get_column(self, attr, filter_valid=True,
                   merge_infrequent=False, return_labels=False):

        if attr is None:
            return None

        needs_merging = \
            attr.is_discrete \
            and merge_infrequent and len(attr.values) >= MAX_CATEGORIES
        if return_labels and not needs_merging:
            assert attr.is_discrete
            return attr.values

        all_data = self.data.get_column_view(attr)[0]
        if all_data.dtype == object and attr.is_primitive():
            all_data = all_data.astype(float)
        if filter_valid and self.valid_data is not None:
            all_data = all_data[self.valid_data]
        if not needs_merging:
            return all_data

        dist = bincount(all_data, max_val=len(attr.values) - 1)[0]
        infrequent = np.zeros(len(attr.values), dtype=bool)
        infrequent[np.argsort(dist)[:-(MAX_CATEGORIES - 1)]] = True
        if return_labels:
            return [value for value, infreq in zip(attr.values, infrequent)
                    if not infreq] + ["Other"]
        else:
            result = all_data.copy()
            freq_vals = [i for i, f in enumerate(infrequent) if not f]
            for i, infreq in enumerate(infrequent):
                if infreq:
                    result[all_data == i] = MAX_CATEGORIES - 1
                else:
                    result[all_data == i] = freq_vals.index(i)
            return result

    def get_palette(self):
        """
        Return a palette suitable for the current `attr_color`
        This method must be overridden if the widget offers coloring that is
        not based on attribute values.
        """
        if self.attr_color is None:
            return None
        colors = self.attr_color.colors
        #print("number of colors", len(colors))
        if self.attr_color.is_discrete:
            return ColorPaletteGenerator(
                number_of_colors=min(len(colors), MAX_CATEGORIES),
                rgb_colors=colors if len(colors) <= MAX_CATEGORIES
                else DefaultRGBColors)
        else:
            return ContinuousPaletteGenerator(*colors)

    def get_color_data(self):
        return self.get_column(self.attr_color, merge_infrequent=True)

    def get_color_labels(self):
        return self.get_column(self.attr_color, merge_infrequent=True,
                               return_labels=True)

    def get_colors(self):
        print("get colors")
        self.palette = self.get_palette()
        c_data = self.get_color_data()
        subset = None  # self.get_subset_mask()
        self.subset_is_shown = subset is not None
        if c_data is None:  # same color
            return self._get_same_colors(subset)
        elif self.is_continuous_color():
            return self._get_continuous_colors(c_data, subset)
        else:
            return self._get_discrete_colors(c_data, subset)

    def _get_continuous_colors(self, c_data, subset):
        print("get _get_continuous_colors")
        if np.isnan(c_data).all():
            self.scale = None
        else:
            self.scale = DiscretizedScale(np.nanmin(c_data), np.nanmax(c_data))
            c_data -= self.scale.offset
            c_data /= self.scale.width
            c_data = np.floor(c_data) + 0.5
            c_data /= self.scale.bins
            c_data = np.clip(c_data, 0, 1)
        pen = self.palette.getRGB(c_data)
        brush = np.hstack(
            [pen, np.full((len(pen), 1), self.alpha_value, dtype=int)])
        pen *= 100
        pen //= DarkerValue
        pen = [_make_pen(QColor(*col), 1.5) for col in pen.tolist()]

        if subset is not None:
            brush[:, 3] = 0
            brush[subset, 3] = 255
        brush = np.array([QBrush(QColor(*col)) for col in brush.tolist()])
        return pen, brush

    def _get_discrete_colors(self, c_data, subset):
        print("get _get_discrete_colors")
        n_colors = self.palette.number_of_colors
        c_data = c_data.copy()
        c_data[np.isnan(c_data)] = n_colors
        c_data = c_data.astype(int)
        colors = np.r_[self.palette.getRGB(np.arange(n_colors)),
                       [[128, 128, 128]]]
        pens = np.array(
            [_make_pen(QColor(*col).darker(DarkerValue), 1.5)
             for col in colors])
        pen = pens[c_data]
        alpha = self.alpha_value if subset is None else 255
        print("alpha ", alpha)
        brushes = np.array([
            [QBrush(QColor(0, 0, 0, 0)),
             QBrush(QColor(col[0], col[1], col[2], alpha))]
            for col in colors])
        brush = brushes[c_data]

        if subset is not None:
            brush = np.where(subset, brush[:, 1], brush[:, 0])
        else:
            brush = brush[:, 1]
        return pen, brush

    def _get_same_colors(self, subset):
        color = QColor(0, 0, 0, 255)

        pen = [_make_pen(color, 1.5) for _ in range(self.n_contours)]
        if subset is not None:
            brush = np.where(
                subset,
                *(QBrush(QColor(*col))
                  for col in (COLOR_SUBSET, COLOR_NOT_SUBSET)))
        else:
            color = QColor(*COLOR_DEFAULT)
            color.setAlpha(self.alpha_value)
            brush = [QBrush(color) for _ in range(self.n_contours)]
        return pen, brush

    def update_colors(self):
        if self.scatterplot_item is not None:
            pen_data, brush_data = self.get_colors()
            self.scatterplot_item.setPen(pen_data, update=False, mask=None)
            self.scatterplot_item.setBrush(brush_data, mask=None)
        self.update_legends()

    # Labels
    def get_labels(self):
        return self._filter_visible(self.get_label_data())

def _make_pen(color, width):
    p = QPen(color, width)
    p.setCosmetic(True)
    return p


if __name__ == "__main__":  # pragma: no cover

    data = Table("iris")
    WidgetPreview(OWCellsViewer).run(set_data=data)
