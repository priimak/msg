import sys
from typing import Any, override

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QPersistentModelIndex
from PySide6.QtWidgets import QApplication, QLabel, QTableView, QAbstractItemView, QWidget, QHBoxLayout, QHeaderView
from inctrl import list_instruments, oscilloscope
from inctrl.model import ISpec
from pytide6 import MainWindow, VBoxPanel, W, HBoxPanel, PushButton, ComboBox, HBoxLayout


class App:
    def __init__(self):
        self.instruments: list[ISpec] = []


def ispec_index_to_value(ispec: ISpec, index: int) -> str:
    match index:
        case 0:
            return ispec.address
        case 1:
            return ispec.make
        case 2:
            return ispec.model
        case 3:
            return ispec.instrument_type.value
        case _:
            return ""


class InstrumentsFrameModel(QAbstractTableModel):
    def __init__(self, app: App):
        super().__init__()
        self.app = app

    @override
    def headerData(self, section: int, orientation: Qt.Orientation, role = ...) -> Any:
        return "Instrument"

    @override
    def rowCount(self, parent = ...) -> int:
        return len(self.app.instruments)

    @override
    def columnCount(self, parent = ...) -> int:
        return 4

    @override
    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = 1) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return ispec_index_to_value(self.app.instruments[index.row()], index.column())

class ScopeControlWindow(QWidget):
    def __init__(self, scope_address: str):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window)
        self.channel = [1]
        
        def select_channel(channel_str):
            self.channel.clear()
            self.channel.append(int(channel_str))
            
        def download_and_show_waveform():
            scope = oscilloscope(scope_address)
            ch = scope.channel(self.channel[0])
            ch.get_waveform().plot(block = False)

        self.setLayout(HBoxLayout([
            ComboBox(items = ["1", "2", "3", "4", "5", "6", "7", "8"], on_text_change = select_channel),
            PushButton("Download waveform", on_clicked = download_and_show_waveform)
        ]))
        
class MSGWindow(MainWindow):
    def __init__(self):
        super().__init__(objectName = "MainWindow", windowTitle = "Mini Scope GUI")
        self.app: App = App()

        self.instruments_frame_model = InstrumentsFrameModel(self.app)
        instruments_view = QTableView(self)
        instruments_view.setModel(self.instruments_frame_model)

        def list_instruments_gui():
            self.app.instruments.clear()
            print("Scanning for connected instruments...")
            instruments = list_instruments()
            self.app.instruments.extend(instruments)

            self.instruments_frame_model.layoutChanged.emit()
            instruments_view.resizeColumnsToContents()
            instruments_view.clearSelection()

        def show_instrument_control():
            idx = instruments_view.selectedIndexes()
            # self.app.instruments[idx[0].row()].address
            window = ScopeControlWindow(self.app.instruments[idx[0].row()].address)
            window.show()
            
        instruments_view.horizontalHeader().setVisible(True)
        instruments_view.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        instruments_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        instruments_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        instruments_view.doubleClicked.connect(show_instrument_control)

        self.setCentralWidget(
            VBoxPanel(
                widgets = [
                    HBoxPanel([
                        PushButton("List Instruments", on_clicked = list_instruments_gui), W(QLabel(""), stretch = 1),
                        PushButton("Quit", on_clicked = self.close)]),
                    W(VBoxPanel([instruments_view]), stretch = 1)
                ],
                spacing = 0, margins = (5, 5, 5, 1)
            )
        )


def main():
    app = QApplication(sys.argv)
    win = MSGWindow()
    win.show()
    win.activateWindow()
    win.raise_()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
