# -*- coding: utf-8 -*-

import os
from pathlib import Path

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw

from .propwin import PropWindow
from .tagselectwin import TagSelectWindow
from .tageditwin import TagEditWindow

from ..events import LoadResReq, SaveResReq, NewViewProps, ReposUpdated


class MainMenuBar(qw.QMenuBar):
    """Main menu bar with drag drop functionality
    Options visible in the setgtool main window
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.last_dir = os.getcwd()

        # thanks, obama (seems to be needed for pyqt on Win)
        self.setNativeMenuBar(False)

        self.view_props_win = None
        #TODO should be stored only once...
        self.view_props = {'rows': 2,
                           'cols': 2,
                           'crosshair': False,}

        self.tag_selection = [set([]), set([])]

        ## DATA
        # quit the app action
        self.act_quit_app = qw.QAction(' &Quit', self)
        self.act_quit_app.setShortcut('Ctrl+Q')
        self.act_quit_app.setStatusTip('Bye, bye!')

        # load the data action
        self.act_load_imagedir = qw.QAction(' Load &Directory...', self)
        self.act_load_imagedir.setShortcut('Ctrl+L')
        self.act_load_imagedir.setStatusTip(
            'Load marker data from images in a directory')

        # load image selection
        self.act_load_imagesel = qw.QAction(' Load &Selection...', self)
        self.act_load_imagesel.setShortcut('Ctrl+S')
        self.act_load_imagesel.setStatusTip(
            'Load marker data from a selection of images')

        # create objects option
        self.act_create_obj = qw.QAction(' Generate from &map...', self)
        self.act_create_obj.setShortcut('Ctrl+M')
        self.act_create_obj.setStatusTip(
            'Create objects from a grayscale image')

        # load objects option
        self.act_load_obj = qw.QAction(' Load &zipped objects...', self)
        self.act_load_obj.setShortcut('Ctrl+Z')
        self.act_load_obj.setStatusTip(
            'Restores objects from a previously generated zipfile')

        # load tags from csv
        self.act_load_tags = qw.QAction(' Load object &tags...', self)
        self.act_load_tags.setShortcut('Ctrl+T')
        self.act_load_tags.setStatusTip(
            'Set tags for objects from CSV file')

        # load objects option
        self.act_save_obj = qw.QAction(' &Save as zipped objects...', self)
        self.act_save_obj.setShortcut('Ctrl+S')
        self.act_save_obj.setStatusTip(
            'Stores objects inlcuding the mapping to a zipfile')

        # data stuff and the quit
        self.menu_data = self.addMenu('&Data')
        self.menu_data.addAction(self.act_quit_app)

        self.menu_image = self.addMenu('&Images')
        self.menu_image.addAction(self.act_load_imagedir)
        self.menu_image.addAction(self.act_load_imagesel)

        self.menu_obj = self.addMenu('&Objects')
        self.menu_obj.addAction(self.act_load_tags)
        self.menu_obj.addAction(self.act_create_obj)
        self.menu_obj.addAction(self.act_load_obj)
        self.menu_obj.addSeparator()
        self.menu_obj.addAction(self.act_save_obj)

        ## MAPPINGS
        # generate tag mappings
        self.act_select_tags = qw.QAction(' Map from &tags...', self)
        self.act_select_tags.setShortcut('Ctrl+T')
        self.act_select_tags.setStatusTip(
            'Create overlay maps from object tags')

        # load maps
        self.act_load_map = qw.QAction(' Load maps from &image...', self)
        self.act_load_map.setShortcut('Ctrl+I')
        self.act_load_map.setStatusTip(
            'Load overlay maps from imagefile')

        # add remove tags
        self.act_edit_tags = qw.QAction(' &Edit tagselection...', self)
        self.act_edit_tags.setShortcut('Ctrl+E')
        self.act_edit_tags.setStatusTip('Edit, add or remove tags')

        # mapping stuff
        self.menu_mapping = self.addMenu('&Mapping')
        self.menu_mapping.addAction(self.act_select_tags)
        self.menu_mapping.addAction(self.act_load_map)
        self.menu_mapping.addSeparator()
        self.menu_mapping.addAction(self.act_edit_tags)

        ## VIEW
        # properties for the view windows
        self.act_view_props = qw.QAction(' &Properties', self)
        self.act_view_props.setShortcut('Ctrl+P')
        self.act_view_props.setStatusTip('Bye, bye!')

        # view stuff
        self.menu_view = self.addMenu('&View')
        self.menu_view.addAction(self.act_view_props)

        # connect stuff
        self.act_load_imagedir.triggered.connect(self.spawn_dirdialog)
        self.act_load_imagesel.triggered.connect(self.spawn_seldialog)
        self.act_create_obj.triggered.connect(self.spawn_mapdialog)
        self.act_load_obj.triggered.connect(self.spawn_objdialog)
        self.act_load_tags.triggered.connect(self.spawn_tagdialog)
        self.act_save_obj.triggered.connect(self.save_objdialog)
        self.act_view_props.triggered.connect(self.show_prop_win)
        self.act_select_tags.triggered.connect(self.show_tagselect_win)
        self.act_edit_tags.triggered.connect(self.show_tagedit_win)
        self.act_load_map.triggered.connect(self.spawn_mapfiledialog)

    @qc.pyqtSlot()
    def spawn_dirdialog(self):
        """shows the dir loading dialog
        """
        dir_path = qw.QFileDialog.getExistingDirectory(
            parent=None,
            caption='Select directory...',
            directory=self.last_dir,
            options=qw.QFileDialog.Options(0),
        )
        if Path(dir_path).exists() and dir_path != '':
            self.last_dir = dir_path
            request = LoadResReq(res_type='img.dir', res_path=dir_path)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def spawn_mapfiledialog(self):
        """shows the map loading dialog
        """
        map_path_list, _ = qw.QFileDialog.getOpenFileNames(
            parent=None,
            caption='Select image file(s)...',
            directory=self.last_dir,
            filter='Objectmap (*.png *.tif *.tiff)',
        )
        valid_paths = []
        for map_path in map_path_list:
            if Path(map_path).exists() and not Path(map_path).is_dir():
                valid_paths.append(str(map_path))
                self.last_dir = str(Path(map_path).parent)

        if valid_paths:
            request = LoadResReq(res_type='overlay.map', res_pathes=valid_paths)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def spawn_mapdialog(self):
        """shows the obj_map loading dialog
        """
        map_path, _ = qw.QFileDialog.getOpenFileName(
            parent=None,
            caption='Select object map...',
            directory=self.last_dir,
            filter='Objectmap (*.png *.tif *.tiff)',
        )
        if Path(map_path).exists() and map_path != '':
            self.last_dir = str(Path(map_path).parent)
            request = LoadResReq(res_type='obj.map', res_path=map_path)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def spawn_seldialog(self):
        """shows the image selection dialog
        """
        image_path_list, _ = qw.QFileDialog.getOpenFileNames(
            parent=None,
            caption='Select images...',
            directory=self.last_dir,
            filter='Images (*.png *.tif *.tiff)',
        )
        valid_paths = []
        for img_path in image_path_list:
            if Path(img_path).exists() and not Path(img_path).is_dir():
                valid_paths.append(str(img_path))
                self.last_dir = str(Path(img_path).parent)

        if valid_paths:
            request = LoadResReq(res_type='img.sel', res_pathes=valid_paths)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def spawn_objdialog(self):
        """shows the obj.zip loading dialog
        """
        zip_path, _ = qw.QFileDialog.getOpenFileName(
            parent=None,
            caption='Select saved objects...',
            directory=self.last_dir,
            filter='Objects (*.obj.zip)',
        )
        if Path(zip_path).exists() and zip_path != '':
            self.last_dir = str(Path(zip_path).parent)
            request = LoadResReq(res_type='obj.zip', res_path=zip_path)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def spawn_tagdialog(self):
        """read and parse data from orange csv
        """
        tag_path, _ = qw.QFileDialog.getOpenFileName(
            parent=None,
            caption='Select csv with tag info',
            directory=self.last_dir,
            filter='CSV (*.csv)',
        )
        if Path(tag_path).exists() and tag_path != '':
            self.last_dir = str(Path(tag_path).parent)
            request = LoadResReq(res_type='obj.tag', res_path=tag_path)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def save_objdialog(self):
        """shows the obj.zip saving dialog
        """
        zip_file, _ = qw.QFileDialog.getSaveFileName(
            parent=None,
            caption='Save objects to...',
            directory=self.last_dir,
            filter='Objects (*.obj.zip)',
        )
        if Path(zip_file).parent.exists() and zip_file != '':
            self.last_dir = str(Path(zip_file).parent)

            if not zip_file.endswith('.obj.zip'):
                zip_file = '{}.obj.zip'.format(zip_file)
            request = SaveResReq(res_type='obj.zip', res_path=zip_file)
            qc.QCoreApplication.postEvent(self.parent(), request)

    @qc.pyqtSlot()
    def show_prop_win(self):
        self.view_props_win = PropWindow(
            view_props=self.view_props,
            parent=self,)
        self.view_props_win.show()

    @qc.pyqtSlot()
    def show_tagselect_win(self):
        all_tags = self.tag_selection[0].union(self.tag_selection[1])
        self.tagselect_win = TagSelectWindow(
            tag_selection=all_tags,
            parent=self,)
        self.tagselect_win.show()

    @qc.pyqtSlot()
    def show_tagedit_win(self):
        self.tagedit_win = TagEditWindow(
            custom_tags=self.tag_selection[1],
            parent=self,)
        self.tagedit_win.show()

    def update_tags(self, event):
        callback = event.repos['tags']
        obj_tags, custom_tags = callback()
        self.tag_selection = set(obj_tags), set(custom_tags)

    def customEvent(self, event):
        if event == NewViewProps:
            self.view_props.update(event.view_props)
            event.ignore()
        elif event == ReposUpdated:
            self.update_tags(event)
        else:
            event.ignore()
