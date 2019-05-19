import os
import sys

# from AnyQt import QtGui, QtCore, QtWidgets
# import AnyQt.QtCore as qc
# import AnyQt.QtWidgets as qw

# from Orange.widgets.utils.sql import check_sql_input

from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets import gui
from Orange.data import Table as OTable
from Orange.widgets.settings import (
    Setting, ContextSetting, DomainContextHandler, SettingProvider)

from Orange.widgets.utils.itemmodels import DomainModel
from Orange.widgets.utils.sql import check_sql_input
from Orange.statistics.util import bincount
from Orange.widgets.utils.colorpalette import (
    ColorPaletteGenerator, ContinuousPaletteGenerator, DefaultRGBColors)

import numpy as np


try:
    from cellinspector import Controller
except ImportError as err:
    if __name__ == '__main__':
        # if run directly, this is propably for debugging reasons and therfor
        # we can assume the directory structure as found in the src dir
        # hence an relative import is needed, to avoid reinstalling all the time
        from pathlib import Path
        import sys

        modpath = Path('../../../../').absolute().resolve()
        sys.path.insert(0, str(modpath))  
    else:
        raise err

    from cellinspector import Controller


class OWCellInpspector(OWWidget):
    name = "Cellinspector"
    description = "Randomly selects a subset of instances from the dataset"
    icon = "icons/DataSamplerA.svg"
    priority = 10

    # # Should the widget construct a mainArea
    # want_main_area = True
    # # Should the widget construct a controlArea.
    # want_control_area = True

    settingsHandler = DomainContextHandler()
    attr_contour = ContextSetting(None)
    attr_eid = ContextSetting(None)
    attr_color = ContextSetting(None)
    selection = Setting(None, schema_only=True)
    show_legend = False
    background_image_enabled = False
    # too_many_labels = Signal(bool)
    graph_name = "scene"
    autocommit = False

    class Inputs:
        entities = Input('Contours', OTable)

    class Outputs:
        sample = Output("Sampled Data", OTable)

    class Error(OWWidget.Error):
        no_valid_contours = Msg("No contours due to no valid data.")

    def __init__(self):
        super().__init__()
        
        self.controller = Controller()
        self.controller.viewer.setGridlayout(2, 2)
        self.scene = self.controller.viewer.entity_scn

        # self.settingsHandler = DomainContextHandler()
        # self.attr_contour = ContextSetting(None)
        # self.attr_label = ContextSetting(None)
        # self.attr_color = ContextSetting(None)
        # self.selection = Setting(None, schema_only=True)
        # self.show_legend = False
        self.background_image_enabled = False
        # # self.too_many_labels = Signal(bool)
        # self.graph_name = "scene"
        # self.autocommit = False
        
        #TODO cleanup
        self.entity_contours = None
        self.entity_ids = None

        self.contours = None
        self.legend = None
        self.n_contours = 0
        self.subset_is_shown = False
        self.alpha_value = 50
        self.zoom_value = 250
        self.label_only_selection = False
        self.labels = []
        self._too_many_labels = False

        self.setup_gui()

    def setup_gui(self):
        """Sets mainArea and the controlArea
        """
        # just add the viewer to the mainArea and we are done
        # with it
        mainlayout = self.mainArea.layout()
        mainlayout.addWidget(self.controller.viewer)
        
        # and the control area
        #TODO into a seperate class or into a factory function
        layout = gui.vBox(self.controlArea, True)

        self.contour_var = DomainModel(
            placeholder='None', separators=False)
        cb_attr_contour = gui.comboBox(
            layout, self, 'attr_contour', label='Contour:',
            model=self.contour_var, callback=self._entities_changed)

        self.eid_var = DomainModel(
            placeholder='None', separators=False)
        cb_attr_eid = gui.comboBox(
            layout, self, 'attr_eid', label='IDs:',
            model=self.eid_var, callback=self._entities_changed)

        self.color_var = DomainModel(
            placeholder='None', separators=False)
        cb_attr_color = gui.comboBox(
            layout, self, 'attr_color', label='Color:',
            model=self.color_var, callback=self._entities_changed)
        
        # adds an stretch
        gui.rubber(layout)
        
        # send selected cells to output
        gui.auto_commit(self.controlArea, self, "autocommit", "Send Selected",
                        "Send Automatically", box=False)

    def _entities_changed(self):
        """Set contour data after user selected
        """
        # no data
        if self.entity_data is None:
            return
        
        # get data columns from contour data and raise an error
        # if none can be extracted
        entity_contours = get_column(self.entity_data, self.attr_contour)
        entity_ids = get_column(self.entity_data, self.attr_eid)
        # no data
        if entity_contours is None or entity_ids is None:
            self.Error.clear()
            return
        
        contour_data = {}
        try:
            for eid, contour_paths in zip(entity_ids, entity_contours):
                print(eid, contour_paths)
        except (TypeError, IndexError):
            self.Error.no_valid_contours()
            return

        # clear all enteties as we use new dataset now...
        self.controller.clearEntities()

        # # pen_data, brush_data = self.get_colors()
        # for row in column_data:
        #     for contour in split(" ")
        #     poly = QPolygonF()
        #     for p in path:
        #         coord = p.split(",")

        #         if len(coord) is not 2:
        #             self.Error.no_valid_contours()
        #             return

        #         point = QtCore.QPointF(float(coord[0]), float(coord[1]))
        #         poly.append(point)

        # # self.Error.clear()
        # # cont_color = self.is_continuous_color()
        # # color_labels = None if cont_color else self.get_color_labels()

    def _on_attr_color_changed(self, *args, **kwargs):
        print(args, kwargs)

    def update_legend_visibility(self, *args, **kwargs):
        print(args, kwargs)

    def _opacity_changed(self, *args, **kwargs):
        print(args, kwargs)

    def _zoom_changed(self, *args, **kwargs):
        print(args, kwargs)

    def _bg_image_enabled(self, *args, **kwargs):
        print(args, kwargs)

    def get_colors(self, max_cat=15):
        print("get colors")
        self.palette = self.get_palette(max_cat)
        c_data = self.get_color_data()
        subset = None  # self.get_subset_mask()
        self.subset_is_shown = subset is not None
        if c_data is None:  # same color
            return self._get_same_colors(subset)
        elif self.is_continuous_color():
            return self._get_continuous_colors(c_data, subset)
        else:
            return self._get_discrete_colors(c_data, subset)

    def get_palette(self, max_cat=15):
        """
        Return a palette suitable for the current `attr_color`
        This method must be overridden if the widget offers coloring that is
        not based on attribute values.
        """
        if self.attr_color is None:
            return None
        colors = self.attr_color.colors
        if self.attr_color.is_discrete:
            return ColorPaletteGenerator(
                number_of_colors=min(len(colors), max_cat),
                rgb_colors=colors if len(colors) <= max_cat
                else DefaultRGBColors)
        else:
            return ContinuousPaletteGenerator(*colors)
        
    @Inputs.entities
    @check_sql_input
    def set_entities(self, entity_data):
        """set data domains to select from
        """
        
        if entity_data is not None:
            self.entity_data = entity_data
            # sets selection options according to contour_data
            self.contour_var.set_domain(self.entity_data.domain)
            self.eid_var.set_domain(self.entity_data.domain)
            self.color_var.set_domain(self.entity_data.domain)

    def commit(self):
        if self.data is not None:
            ids = []
            for c in self.contours:
                if c._selected:
                    ids.append(c.id)
                    self.data[c.id]["Selected"] = True
                else:
                    self.data[c.id]["Selected"] = False
            self.Outputs.selected_data.send(self.data[ids])
            self.Outputs.data.send(self.data)
        else:
            self.Outputs.selected_data.send(None)
            self.Outputs.data.send(None)


def get_column(dataset, attr):
    
    # nothing happens...
    if attr is None:
        return None

    needs_merging = attr.is_discrete and merge_infrequent \
                    and len(attr.values) >= max_cat

    if not needs_merging:
        return attr.values

    all_data = dataset.get_column_view(attr)[0]
    if all_data.dtype == object and attr.is_primitive():
        all_data = all_data.astype(float)
    if filter_valid and self.valid_data is not None:
        all_data = all_data[self.valid_data]
    
    if not needs_merging:
        return all_data

    dist = bincount(all_data, max_val=len(attr.values) - 1)[0]
    infrequent = np.zeros(len(attr.values), dtype=bool)
    infrequent[np.argsort(dist)[:-(max_cat - 1)]] = True
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


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    data = OTable("iris")
    WidgetPreview(OWCellInpspector).run(set_entities=data)
