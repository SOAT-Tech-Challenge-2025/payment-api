"""Port interface for QR code rendering use case"""

from abc import ABC, abstractmethod


class QRCodeRenderer(ABC):
    """Interface for rendering QR codes."""

    @abstractmethod
    def render(self, data: str) -> bytes:
        """Render a QR code from the given data string.

        :param data: The data to encode in the QR code.
        :type data: str
        :return: The rendered QR code as a byte array.
        :rtype: bytes
        """
