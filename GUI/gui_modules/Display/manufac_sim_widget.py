from PyQt5.QtWidgets import QWidget, QTableWidget, QStyledItemDelegate, QAbstractItemView, QHeaderView, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QComboBox, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp
from PyQt5.QtGui import QRegExpValidator, QPainter, QColor


class ManufacSimWidget(QWidget):
    '''
    Widget for maunufacting simulation
    '''
    applySimData = pyqtSignal(list)

    class DraggableTableWidget(QTableWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDragDropMode(QAbstractItemView.InternalMove)
            self.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.setSelectionMode(QAbstractItemView.SingleSelection)
            self.setDropIndicatorShown(True)
            self.setShowGrid(True)

        def dropEvent(self, event):
            if event.source() == self:
                super().dropEvent(event)
                self.viewport().update()

    class ColorBlockDelegate(QStyledItemDelegate):
        def paint(self, painter, option, index):
            if index.data(Qt.UserRole):
                color = index.data(Qt.UserRole)
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(color))
                painter.drawRect(option.rect.adjusted(2, 2, -2, -2))
                painter.restore()

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Maunufacting Simulation")
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            int(screen.width() * 0.25),
            int(screen.height() * 0.25),
            int(screen.width() * 0.5),
            int(screen.height() * 0.5)
        )
        self.setMinimumSize(600, 400)
        self.table = ManufacSimWidget.DraggableTableWidget(self)
        # set header
        self.headers = ["Name", "Color", "Layer",
                        "Datatype", "Process", "Depth"]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # set delegate
        self.table.setItemDelegateForColumn(
            1, ManufacSimWidget.ColorBlockDelegate())

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        apply_bt = QPushButton("Apply", self)
        clear_bt = QPushButton("Clear", self)
        cancel_bt = QPushButton("Cancel", self)
        button_layout.addWidget(apply_bt)
        button_layout.addWidget(clear_bt)
        button_layout.addWidget(cancel_bt)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # connect apply button
        apply_bt.pressed.connect(self._sendSimData)
        # connect cancel button
        cancel_bt.pressed.connect(self.hide)

    def setData(self, data: list):
        self.table.clearContents()
        self.table.setRowCount(len(data))
        for row, item_data in enumerate(data):
            # color
            color_item = QTableWidgetItem()
            color_item.setData(Qt.UserRole, item_data.get('Color', '#FF0000'))
            color_item.setFlags(color_item.flags() & ~
                                Qt.ItemIsEditable)  # non editable
            self.table.setItem(row, 1, color_item)

            # layer
            self.table.setItem(
                row, 2, QTableWidgetItem(str(item_data.get('Layer'))))
            self.table.item(row, 2).setFlags(
                self.table.item(row, 2).flags() & ~ Qt.ItemIsEditable)
            # datatype
            self.table.setItem(row, 3, QTableWidgetItem(
                str(item_data.get('Datatype'))))
            self.table.item(row, 3).setFlags(
                self.table.item(row, 3).flags() & ~ Qt.ItemIsEditable)

            # combobox
            combo = QComboBox()
            combo.addItems(["CVD", "Etching"])
            combo.setCurrentText(item_data.get('Process', 'CVD'))
            self.table.setCellWidget(row, 4, combo)

            # float editor
            value_edit = QLineEdit()
            validator = QRegExpValidator(
                QRegExp(r"[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?"))
            value_edit.setValidator(validator)
            value_edit.setText(str(item_data.get('Depth', 0.0)))
            self.table.setCellWidget(row, 5, value_edit)

    def _getTabelData(self):
        data = []
        row_count = self.table.rowCount()
        column_count = self.table.columnCount()

        for row in range(row_count):
            row_data = {}
            for col in range(len(self.headers)):
                if self.headers[col] == "Process":
                    cell_widget = self.table.cellWidget(row, col)
                    elem = cell_widget.currentText()
                elif self.headers[col] == "Depth":
                    cell_widget = self.table.cellWidget(row, col)
                    elem = cell_widget.text()
                else:
                    item = self.table.item(row, col)
                    if item is not None and item.text():
                        elem = item.text()
                    else:
                        elem = item
                row_data[self.headers[col]] = elem
            data.append(row_data)

        return data
    
    def _sendSimData(self):
        self.applySimData.emit(self._getTabelData())
        self.hide()


if __name__ == "__main__":
    import sys
    import os
    from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QApplication
    current_path = os.path.dirname(os.path.abspath(__file__))
    PROJ_PATH = os.path.abspath(os.path.join(
        os.path.dirname(current_path), "../.."))
    sys.path.append(PROJ_PATH)
    app = QApplication([])
    test_data = [
        {'Color': '#FF0000', 'Layer': 1, 'Process': 'CVD', 'Depth': 3.14},
        {'Color': '#00FF00', 'Layer': 2, 'Process': 'Etching', 'Depth': 2.718},
        {'Color': '#0000FF', 'Layer': 3, 'Process': 'Etching', 'Depth': 1.618},
        {'Color': '#FFFF00', 'Layer': 4, 'Process': '选项B', 'Depth': 0.577},
        {'Color': '#FF00FF', 'Layer': 5, 'Process': 'CVD', 'Depth': 1.414}
    ]
    widget = ManufacSimWidget()
    widget.setData(test_data)
    widget._getTabelData()
    widget.show()
    sys.exit(app.exec_())
