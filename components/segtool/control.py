# -*- coding: utf-8 -*-

"""Controller of the app. Intermediates between model and view, owns both
"""
import sys
import logging
from pathlib import Path

import PyQt5.QtWidgets as qw
import PyQt5.QtCore as qc

from .view import DataViewer
from .view.console import QIPythonWidget
from .data import DataManager

from .util import CallBack, parse_orange

from .events import ReposUpdated, ErrorEvent

from ._config import __marker_db_dir as db_dir


class RepoManager(qc.QObject):
    """ Mainly to keep callbacks elements alive
    merge all feature functions into this class? or
    merge AppControl asn this class again?
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inject dependencies here
        self.repos = {
            'bg': {},
            'fg': {},
            'tags': [],
            'misc': {},
            }

        self.receiver = []

    def update_repo(self, post=True, wipe=True, **kwargs):

        for key, new_repo in kwargs.items():
            if not key in self.repos:
                raise ValueError('Invalid repo key')
            self.repos[key] = new_repo
        if post:
            self.post_receiver(wipe=wipe)

    def post_receiver(self, wipe):
        the_app = qc.QCoreApplication
        repos_updated = ReposUpdated(self.repos, wipe=wipe)
        for recv in self.receiver:
            the_app.postEvent(recv, repos_updated)


class AppControl(qw.QApplication):
    """Controller class, owning the DataManager and DataView, sets and
    manages the databinding, owns the proxyadapter
    """

    def __init__(self, *args, console=False, loglevel=logging.DEBUG, **kwargs):
        super().__init__(*args, **kwargs)

        # set logger
        self.log = logging.getLogger('AppControl')
        self.log.info('Init...')
        logging.getLogger('').setLevel(loglevel)
        #TODO logging Handler for statusbar

        # set datamanager aka model

        abid_db_path = self._get_abid_db()
        self.log.info('Starting DataManager...')
        self.datamanager = DataManager(logger_name='DataManager',
                                       marker_db_path=abid_db_path)

        # set dataviewer aka viewer
        self.log.info('Starting DataViewer...')
        self.dataviewer = DataViewer(parent=self)
        # self.dataviewer.mainview.showFullScreen()
        self.dataviewer.show()

        # set dataviewer aka viewer
        self.log.info('Binding components...')
        self.binding_components()

        # event passing/handling
        self.log.info('Arming Trigger...')
        self.repomanager = RepoManager()
        self.repomanager.receiver.append(self.dataviewer)
        # init first empty repos
        self.update_view()

        self.console = None
        if console:
            self._spawn_console()

        self.log.info('App Initialized')

        # if loglevel == logging.DEBUG:
        #     banner = '\n{:=>50s}\n=={: ^46s}==\n{:=>50s}\n'
        #     msg = banner.format('', 'DEBUG MODE - Assuming res!', '')
        #     self.log.warn(msg)
        #     self._ff_load_image_dir('./res/data/real_fake_doors/')
        #     # self._ff_load_images('C:/Users/andreg/Desktop/elvira_niesl_fld2')
        #     self._ff_load_objzip('./res/data/real_fake_doors/rfd.obj.zip')
        #     timer = qc.QTimer()
        #     timer.singleShot(500, self._finalize)

    def _get_abid_db(self):
        base_cand = [Path('./res/data'),
                     Path(sys.prefix) / db_dir]
        for bcand in base_cand:
            cand = bcand / 'abids.json'
            if cand.exists():
                self.log.info('Using %s as antibody database', str(cand.absolute()))
                return cand
        self.log.error('Could not find any AbID database')
        return None

    @qc.pyqtSlot()
    def _finalize(self):
        view = self.dataviewer.viewgrid.views[0, 0]
        view.load_image('DAPIi', 'bg')

    def _get_bg_repo(self):
        bg_rep = {}
        if self.datamanager.markers_loaded:
            marker_list = self.datamanager.marker_list
        else:
            marker_list = []

        for img_name in marker_list:
            callback = CallBack(self.datamanager.get_raw_image, img_name)
            bg_rep[img_name] = callback

        bg_rep['None'] = self.datamanager.get_empty_image
        return bg_rep

    def _get_fg_repo(self):
        fg_rep = {
            'None': self.datamanager.get_empty_map,}

        #TODO here shoudl only be made the connection between name and call
        #the datamanager generates names and callbacks itselve
        if self.datamanager.objects_loaded:
            fg_rep['Object Mask'] = self.datamanager.get_object_overlay

        for cached_name in self.datamanager.get_cached_names():
            callback = CallBack(self.datamanager.get_by_name, cached_name)
            fg_rep[cached_name] = callback

        return fg_rep

    def _get_tag_repo(self):
        #TODO merge into tag repo
        callback = CallBack(self.datamanager.get_tags)
        return callback

    def _get_misc_repo(self):
        cb_objid = CallBack(self.datamanager.get_object_map)
        cb_obj = CallBack(self.datamanager.get_object)
        repo = {'object_id_map': cb_objid,
                'object': cb_obj,
               }
        return repo

    def update_view(self, wipe=True):
        self.log.debug('Updating view')
        self.repomanager.update_repo(
            bg=self._get_bg_repo(),
            fg=self._get_fg_repo(),
            tags=self._get_tag_repo(),
            misc=self._get_misc_repo(),
            wipe=wipe,
        )

    @qc.pyqtSlot(str)
    def _ff_load_image_dir(self, img_path):
        self.log.info('Loading dir %s', str(img_path))
        self.datamanager.load_imagedir(Path(img_path))

        markers = self.datamanager.marker_list
        markers_found = len(markers)
        self.log.info('Found %d markers:', markers_found)
        self.log.debug('%s', str(markers))

        self.update_view()

    @qc.pyqtSlot(list)
    def _ff_load_overlay_selection(self, path_list):
        img_names = [Path(ipath).name for ipath in path_list]
        self.log.info('Loading map(s) %s', ', '.join(img_names))

        try:
            self.datamanager.load_map_selection(path_list)
        except ValueError:
            msg = 'Could not load images. All images with same dimension?'
            self.log.info(msg)

        self.update_view(wipe=False)

    @qc.pyqtSlot(list)
    def _ff_load_image_selection(self, path_list):
        img_names = [Path(ipath).name for ipath in path_list]
        self.log.info('Loading selection %s', ', '.join(img_names))

        try:
            self.datamanager.load_image_selection(path_list)
            self.update_view(wipe=False)
        except ValueError:
            msg = 'Could not load images. All images with same dimension?'
            self.log.info(msg)

    @qc.pyqtSlot(str)
    def _ff_objects_from_map(self, map_path):
        self.log.info('Creating objects from %s', str(map_path))
        self.datamanager.objects_from_map(Path(map_path))

        object_list = self.datamanager.objects
        object_count = len(object_list)
        self.log.info('Created %d objects', object_count)

        self.update_view(wipe=False)

    @qc.pyqtSlot(str)
    def _ff_save_objzip(self, zip_path):
        self.datamanager.save_object_zip(zip_path)
        self.log.info('Saved %d objects+mapping to %s',
                      len(self.datamanager.objects), str(zip_path))
        self.update_view(wipe=False)

    @qc.pyqtSlot(str)
    def _ff_tags_from_csv(self, csv_path):
        orange_objects = parse_orange(csv_path)
        self.datamanager.update_objects(orange_objects)
        self.update_view(wipe=False)

    @qc.pyqtSlot(str)
    def _ff_load_objzip(self, zip_path):
        try:
            self.datamanager.load_object_zip(zip_path)
        #TODO more real errors
        # also move the save file format to an extra class
        # possibly allowing for all kinds of formats to be read
        except (IOError, IndexError, ValueError) as err:
            self.log.error('Could not load %s with error:\n%s',
                           str(zip_path), str(err))

        loaded_objects = self.datamanager.objects
        self.log.debug('Loaded %d objects from %s', len(loaded_objects),
                       str(zip_path))

        self.update_view(wipe=False)

    @qc.pyqtSlot(list)
    def _ff_update_tags(self, taglist):
        self.datamanager.set_custom_tags(taglist)
        self.update_view(wipe=False)

    @qc.pyqtSlot(int, str)
    def _ff_update_objtag(self, obj_id, tag):
        obj = self.datamanager.get_object(obj_id)
        if tag == 'None':
            self.log.debug('Removing all tags')
            obj.tags.clear()
        elif tag in obj.tags:
            obj.tags.remove(tag)
        else:
            obj.tags.add(tag)

    @qc.pyqtSlot(list, str)
    def _ff_gen_tagoverlay(self, taglist, name):
        try:
            self.datamanager.get_tag_overlay(taglist, name)
            self.update_view(wipe=False)
        except ValueError:
            msg = 'Ambigious tags: {}! Would lead'.format(taglist) + \
                  ' to some objects belonging to multiple clusters!'
            err = ErrorEvent(msg)
            qc.QCoreApplication.postEvent(self.dataviewer, err)

    @qc.pyqtSlot()
    def _ff_not_implementd(self):
        self.log.error('NOT IMPLEMENTED YET')

    def binding_components(self):
        """Binds DataViewer to DataManager by connecting calls and callbacks.
        each feature might be activated or deactivated here
        """
        #TODO could be as well be and dependencie injection or something
        # image dir loading
        self.dataviewer.sig_req_load_imagedir.connect(
            self._ff_load_image_dir)

        # image selection loading
        self.dataviewer.sig_req_load_imagesel.connect(
            self._ff_load_image_selection)

        # object generation from an objectmap
        self.dataviewer.sig_req_load_objmap.connect(
            self._ff_objects_from_map)

        # set object tags from csv
        self.dataviewer.sig_req_load_objtags.connect(
            self._ff_tags_from_csv)

        # loading obj.zip
        self.dataviewer.sig_req_load_objzip.connect(
            self._ff_load_objzip)

        # saving obj.zip
        self.dataviewer.sig_req_save_objzip.connect(
            self._ff_save_objzip)

        # tag overlay map
        self.dataviewer.sig_req_tag_overlay.connect(
            self._ff_gen_tagoverlay)

        # image overlay map
        self.dataviewer.sig_req_load_overlaymaps.connect(
            self._ff_load_overlay_selection)

        # update custom tags
        self.dataviewer.sig_req_modify_tags.connect(
            self._ff_update_tags)

        # change tag of object
        self.dataviewer.sig_req_modify_objtag.connect(
            self._ff_update_objtag)



        # oligatory cleanup
        self.aboutToQuit.connect(self.cleanup)

    # @qc.pyqtSlot()
    # def _ff_update_tags(self, taglist):
    #     self.datamanager.set_custom_tags(taglist)
    #     self.update_view()


    @qc.pyqtSlot()
    def cleanup(self):
        """Cleans all up for gracefull shutdown
        """
        if not self.console is None:
            self.console.close()
            self.console.stop()
        self.log.info('Bye, bye')

    def notify(self, receiver, event):
        if event.type() > qc.QEvent.User:
            candidate = receiver
            while not candidate is None:
                # Note that this calls `event` method directly thus bypassing
                # calling qApplications and receivers event filters
                res = candidate.event(event);
                if res is True and event.isAccepted():
                    return res
                candidate = candidate.parent()

        return super().notify(receiver, event)

    def _spawn_console(self):
        # setting the console
        self.log.info('Starting Console...')

        # mute the ipykernel assiciated logger
        for baselog in ('ipykernel', 'traitlets'):
            log = logging.getLogger(baselog)
            log.setLevel(logging.WARNING)

        # make dialog
        # console_win = qw.QWidget()
        # console_win.setLayout(qw.QVBoxLayout())
        # layout = console_win.layout()

        # console_win.setObjectName('Console')
        # console_win.resize(800, 600)

        # add console
        # console = QIPythonWidget(parent=console_win)
        console = QIPythonWidget()
        # layout.addWidget(console)
        # console_win.setCentralWidget(console)

        # push environment
        console.push_variables({'app': self})

        # store everything
        # console_win.console_widget = console
        # self.console = console_win
        self.console = console

        self.console.show()
        self.console.set_default_style('linux')
