# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 February 2018
# General classes for piping dialogs

from PySide import QtCore


class PartTableModel(QtCore.QAbstractTableModel):
    def __init__(self, headers, data, parent=None, *args):
        self.headers = headers
        self.table_data = data
        self.keyColumnName = None
        QtCore.QAbstractTableModel.__init__(self, parent, *args)

    def rowCount(self, parent):
        return len(self.table_data)

    def columnCount(self, parent):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.table_data[index.row()][index.column()]

    def getPartKey(self, rowIndex):
        key_index = self.headers.index(self.keyColumnName)
        return self.table_data[rowIndex][key_index]

    def getPartRowIndex(self, key):
        """ Return row index of the part with key *key*.

        The *key* is usually refers to the part number.
        :param key: Key of the part.
        :return: Index of the first row whose key is equal to key
                        return -1 if no row find.
        """
        key_index = self.headers.index(self.keyColumnName)
        for row_i in range(key_index, len(self.table_data)):
            if self.table_data[row_i][key_index] == key:
                return row_i
        return -1

    def headerData(self, col, orientation, role):
        if orientation == QtCore. Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[col]
        return None
