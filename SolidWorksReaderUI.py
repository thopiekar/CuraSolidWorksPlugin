# Copyright (c) 2017 Ultimaker B.V.
# Copyright (c) 2017 Thomas Karl Pietrowski
# Cura is released under the terms of the AGPLv3 or higher.

import os
import threading

from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger

from UM.i18n import i18nCatalog

from UM.Preferences import Preferences

catalog = i18nCatalog("SolidWorksPlugin")


class SolidWorksReaderUI(QObject):
    show_config_ui_trigger = pyqtSignal()

    def __init__(self):
        super().__init__()

        Preferences.getInstance().addPreference("cura_solidworks/export_quality", 0)
        Preferences.getInstance().addPreference("cura_solidworks/show_export_settings_always", True)

        self._cancelled = False
        self._ui_view = None
        self.show_config_ui_trigger.connect(self._onShowConfigUI)


        self._ui_lock = threading.Lock()

    def getCancelled(self):
        return self._cancelled

    def waitForUIToClose(self):
        Logger.log("d", "Waitiung for UI to close..")
        self._ui_lock.acquire()
        Logger.log("d", "Got lock and releasing it now..")
        self._ui_lock.release()
        Logger.log("d", "Lock released!")

    def showConfigUI(self, blocking = False):
        self._ui_lock.acquire()
        preference = Preferences.getInstance().getValue("cura_solidworks/show_export_settings_always")
        Logger.log("d", "Showing wizard {} needed.. (preference = {})".format(["is", "is not"][preference], repr(preference)))
        if preference:
            #self.quality = Preferences.getInstance().getValue("cura_solidworks/export_quality")
            self._ui_lock.release()
            return
        self._cancelled = False
        self.show_config_ui_trigger.emit()
        
        if blocking:
            Logger.log("d", "Waitiung for UI to close..")
            self.waitForUIToClose()

    @property
    def quality(self):
        return Preferences.getInstance().getValue("cura_solidworks/export_quality")

    @pyqtSlot(str, bool)
    def setQuality(self, quality, remember_my_choice):
        #self.quality = quality
        Preferences.getInstance().setValue("cura_solidworks/show_export_settings_always", remember_my_choice)
        Preferences.getInstance().setValue("cura_solidworks/export_quality", quality)

    def _onShowConfigUI(self):
        if self._ui_view is None:
            self._createConfigUI()
        self._ui_view.show()

    def _createConfigUI(self):
        if self._ui_view is None:
            path = QUrl.fromLocalFile(os.path.join(os.path.split(__file__)[0], "SolidWorksExportSTLUI.qml"))
            component = QQmlComponent(Application.getInstance()._engine, path)
            self._ui_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._ui_context.setContextProperty("manager", self)
            self._ui_view = component.create(self._ui_context)

            self._ui_view.setFlags(self._ui_view.flags() & ~Qt.WindowCloseButtonHint & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint)

    @pyqtSlot()
    def onOkButtonClicked(self):
        Logger.log("d", "Clicked on OkButton")
        self._cancelled = False
        self._ui_view.close()
        self._ui_lock.release()

    @pyqtSlot()
    def onCancelButtonClicked(self):
        Logger.log("d", "Clicked on CancelButton")
        self._cancelled = True
        self._ui_view.close()
        self._ui_lock.release()
