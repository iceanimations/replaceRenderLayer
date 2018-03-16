import os
import functools

from PyQt4 import uic
from PyQt4 import QtGui as gui
from PyQt4 import QtCore as core


from . import renderlayer


UI_FILE = os.path.join(os.path.dirname(__file__), 'ui.ui')


RL_FORM, RL_BASE = uic.loadUiType(UI_FILE)


class RenderLayerWindow(RL_FORM, RL_BASE):

    def __init__(self):
        super(RenderLayerWindow, self).__init__()
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.applyButton.clicked.connect(self.apply)
        self.refreshButton.clicked.connect(self.refresh)

        self.populate()

    def clear(self):
        self.treeWidget.clear()

    def combo_change(self, top_idx, one_idx, idx):
        rl_item = self.treeWidget.topLevelItem(top_idx).child(one_idx)
        if idx == 0:
            rl_item.setCheckState(0, 0)
        else:
            rl_item.setCheckState(0, 2)

    def mode(self):
        return 'selected' if self.selectionButton.isChecked() else 'all'

    def populate(self):
        render_layers = renderlayer.get_render_layers_from_comp(self.mode())

        top_idx = 0
        for main_dir, rls in render_layers.items():
            dir_item = gui.QTreeWidgetItem()
            self.treeWidget.addTopLevelItem(dir_item)
            dir_item.setText(0, os.path.basename(main_dir))
            dir_item.setExpanded(True)

            one_idx = 0
            for _rl, _list in rls.items():
                path = _list[0]

                _dir, _rl, _ = renderlayer.split_path_until(path)

                dir_item.setToolTip(0, _dir)
                dir_item.setText(1, _dir)

                rl_item = gui.QTreeWidgetItem()
                rl_item.setCheckState(0, 0)
                rl_item.setFlags(
                        rl_item.flags() & ~
                        core.Qt.ItemIsUserCheckable & ~
                        core.Qt.ItemIsTristate)
                rl_item.setText(0, _rl)
                rl_item.setToolTip(0, '%d Read Nodes Found' % len(_list))
                dir_item.addChild(rl_item)
                box = gui.QComboBox()
                box.activated[int].connect(functools.partial(
                    self.combo_change, top_idx, one_idx))
                all_layers = renderlayer.get_render_layers_in_path(path)
                if _rl in all_layers:
                    all_layers.remove(_rl)
                box.addItems([_rl] + all_layers)
                self.treeWidget.setItemWidget(rl_item, 1, box)
                one_idx += 1

            top_idx += 1

        self.treeWidget.setColumnWidth(0, 200)
        self.treeWidget.setColumnWidth(1, 200)

    def refresh(self):
        self.clear()
        self.populate()

    def apply(self):
        self.do()
        self.refresh()

    def reject(self):
        self.close()
        self.deleteLater()

    def accept(self):
        self.do()
        self.close()

    def do(self):
        for top_idx in range(self.treeWidget.topLevelItemCount()):
            dir_item = self.treeWidget.topLevelItem(top_idx)
            main_dir = dir_item.text(1)
            maps = dict()
            for one_idx in range(dir_item.childCount()):
                rl_item = dir_item.child(one_idx)
                if rl_item.checkState(0):
                    box = self.treeWidget.itemWidget(rl_item, 1)
                    rl2 = box.currentText()
                    maps[rl_item.text(0)] = rl2
            renderlayer.replace_render_layers(maps, main_dir, self.mode())
