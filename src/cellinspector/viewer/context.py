from AnyQt import QtGui as qg, QtWidgets as qw, QtCore as qc


class ContextMenu(qg.QMenu):

    sigContextSelected = qc.pyqtSignal(str, str)

    def __init__(self):
        super().__init__()

        menuBg = self.addMenu('Select &Background...')
        self.addSeparator()
        
        #TODO implement me
        menuTag = self.addMenu('Set &Tag...')
        # self.addSeparator()
        # self.enhance = self.addAction('&Enhance BG...')

        # # alpha channel control
        # alpha_menu = self.addMenu('&Opacity')
        # self.alpha_slider = qw.QSlider()
        # self.alpha_slider.setMinimum(0)
        # self.alpha_slider.setMaximum(100)
        # self.alpha_slider.setSingleStep(1)
        # self.alpha_slider.setPageStep(10)
        # alpha_action = qg.QWidgetAction(self)
        # alpha_action.setDefaultWidget(self.alpha_slider)
        # alpha_menu.addAction(alpha_action)
        # self.alpha_slider.valueChanged.connect(self._new_alpha)

        self._menus = {'channelBg': menuBg,
                       'tags': menuTag,}

    def updateSelection(self, names, selector):
        """updates the selection for a given selector
        """
        #TODO better var name for selector
        names = set(names)

        try:
            names.remove('None')
        except KeyError:
            pass # non None entry found
        
        names = list(names)
        names.sort()
        names = ['None'] + names

        # if selector == 'bg':

        menu = self._menus[selector]
        menu.clear()

        for aName in names:
            newAction = menu.addAction(
                aName, self.onSelection)
            # used in the trigger to ask for correct image to load
            newAction.callbackInfo = selector, aName

    @qc.pyqtSlot()
    def onSelection(self):
        aName, selector = self.sender().callbackInfo
        self.sigContextSelected.emit(selector, aName)

        # elif layer_name == 'tags':
        #     self._tag_selection = name_selection
        #     # self._set_tag_selector(name_selection, layer_name)

    # def _set_image_selector(self, names, layer_name):
    #     selector = self.selectors[layer_name]
    #     selector.clear()
    #     for a_name in names:
    #         new_action = selector.addAction(
    #             a_name, self.trig_dat_loading)
    #         # used in the trigger to ask for correct image to load
    #         new_action.callback_info = a_name, layer_name

    # def _set_tag_selector(self):
    #     selector = self.selectors['tags']
    #     selector.clear()
    #     if self.view.over_object <= 0:
    #         return
    #     for a_name in self._tag_selection:
    #         new_action = selector.addAction(
    #             a_name, self.trig_tag_setting)
    #         # used in the trigger to ask for correct image to load
    #         new_action.callback_info = a_name
