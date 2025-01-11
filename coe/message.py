"""
"""

import logging

from typing import Any

from coe import CoEType

logger = logging.getLogger(__name__)


class Message:
    def __init__(self, node: int, address: int, value: Any, datatype: CoEType = CoEType.NONE):
        self._node = node
        self._address = address
        self._value = value
        if type(value) == bool:
            self._datatype = CoEType.ONOFF
        else:
            self._datatype = datatype

    @property
    def node(self) -> int:
        return self._node

    @property
    def address(self) -> int:
        return self._address

    @property
    def value(self) -> Any:
        return self._value

    @property
    def datatype(self) -> CoEType:
        return self._datatype

    @property
    def is_digital(self) -> bool:
        return type(self._value) == bool

    def __str__(self):
        return "CoE message: node: %i, address: %i, value: %s" % (self.node, self.address, self.value)
