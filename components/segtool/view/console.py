import logging
from pathlib import Path

import AnyQt.QtGui as qg
import AnyQt.QtCore as qc

from qtconsole.ipython_widget import JupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport


#TODO make singleton
class ConsoleFont(qg.QFont):
    def __init__(self, pt_size):
        font_path = Path('./res/fonts/DejaVuSansMono.ttf')
        fid = qg.QFontDatabase.addApplicationFont(str(font_path))
        if fid == -1:
            raise ValueError('ConsoleFont not found...')
        font_string = qg.QFontDatabase.applicationFontFamilies(0)[0]
        super().__init__(font_string)
        self.setPointSize(pt_size)


class QIPythonWidget(JupyterWidget):
    """Convenience class for a live IPython console widget"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger('Console')
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        self.banner = u''
        kernel_manager.kernel.shell.banner1 = u''
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        self.font = ConsoleFont(11)

        self.exit_requested.connect(self.stop)

        self.kernel_manager.kernel.shell.push({'console': self})

    def push_variables(self, variable_dict):
        """give some context"""
        self.kernel_manager.kernel.shell.push(variable_dict)
        # self._control.clear()
        # self._append_plain_text(text)
        # self._execute(command, False)

    @qc.pyqtSlot()
    def stop(self):
        self._log.debug('Closing')
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()
