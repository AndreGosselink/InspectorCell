import os
import sys
from pathlib import Path

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


if __name__ == '__main__':
    # if run directly, this is propably for debugging reasons and therfor
    # we can assume the directory structure as found in the src dir
    # hence an relative import is needed, to avoid reinstalling all the time
    from pathlib import Path
    import sys

    modpath = Path('../../../').absolute().resolve()
    sys.path.insert(0, str(modpath))  

from cellinspector import Controller
from cellinspector.graphics import GFX


class OWCellInpspector(OWWidget):
    name = "Cellinspector"
    description = "Randomly selects a subset of instances from the dataset"
    icon = "icons/DataSamplerA.svg"
    priority = 10

    # # Should the widget construct a mainArea
    # want_main_area = True
    # # Should the widget construct a controlArea.
    # want_control_area = True

    attr_contour = ContextSetting(None)
    attr_eid = ContextSetting(None)
    attr_color = ContextSetting(None)
    attrImage = ContextSetting(None)
    autocommit = False

    class Inputs:
        entities = Input('Entities', OTable)
        images = Input('Images', OTable)

    class Outputs:
        sample = Output("Sampled Data", OTable)

    class Error(OWWidget.Error):
        no_valid_contours = Msg("No contours due to no valid data.")

    def __init__(self):
        super().__init__()
        
        self.controller = Controller()
        self.controller.initViewer()

        #TODO cleanup
        self.entity_contours = None
        self.entity_ids = None

        self.contours = None
        self.subset_is_shown = False

        self.setup_gui()

    def setup_gui(self):
        """Sets mainArea and the controlArea
        """
        # just add the viewer to the mainArea and we are done
        # with it
        mainlayout = self.mainArea.layout()
        mainlayout.addWidget(self.controller.viewer)
        
        #FIXME REMOVE AFTER DEBUG!
        widget = self.controller.viewer#TestlWidget()
        
        widget.set_gridlayout(2, 2)
        for i in range(2):
            for j in range(2):
                imdat = np.random.uniform(0, 0xfff, 4096 * 4096)
                imdat = imdat.reshape(4096, 4096).astype(np.uint16)
                bl0, bl1 = np.random.randint(96, 1024, 2)
                bu0, bu1 = np.random.randint(2048, 4000, 2)
                imdat[bl0:bu1, bl1:bu1] *= 2
                widget.set_background((i, j), imdat)

        widget.show_entities((0, 0))
        ### REMOVE AFTER DEBUG!
        
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
        # layoutIcon = self.style().
        self.btnViewLayout = gui.button(layout, self, label='Set Layout',
            callback=self.controller.showViewSetupDialog)

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
        entity_contours_str = get_column(self.entity_data, self.attr_contour)
        entity_ids = get_column(self.entity_data, self.attr_eid)
        # no data
        if entity_contours_str is None or entity_ids is None:
            self.Error.clear()
            return
        
        entity_contours = []
        try:
            for eid, str_contour in zip(entity_ids, entity_contours_str):
                path = []
                for pt_string in str_contour.split(' '):
                    pt_float = list(float(p) for p in pt_string.split(','))
                    path.append(pt_float)
                econ = [np.array(path, float)]
                entity_contours.append((int(eid), econ))
        except (TypeError, IndexError, AttributeError):
            self.Error.no_valid_contours()
            return

        # clear all enteties as we use new dataset now...
        self.controller.clearEntities()
        
        # set entities with parsed contour data
        self.controller.generateEntities(entityContours=entity_contours)

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

    @Inputs.images
    @check_sql_input
    def setImages(self, imageData):
        """Informs the controller which images are availabel
        """
        if not imageData is None:
            choices = []
            for inst in imageData:
                # get all variables from table
                name = inst['image name']
                img = inst['image']
                imgDir = img.variable.attributes.get('origin', '')
                # construct path
                imgPath = Path(str(imgDir)) / str(img)
                # if path exists, append it to choices
                if imgPath.exists():
                    choices.append((str(name), imgPath))
            
            self.controller.setImages(choices)

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
    
    # only use values not sparsity
    values, _ = dataset.get_column_view(attr)
    return values


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    data = OTable("iris")
    WidgetPreview(OWCellInpspector).run(set_entities=data)
