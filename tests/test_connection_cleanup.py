"""Verify stalled DTU connections cannot block subsequent requests."""

import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from hoymiles_wifi.dtu import DTU, NetworkState


class ConnectionCleanupTests(unittest.IsolatedAsyncioTestCase):
    """Bound socket writes and shutdown while releasing the shared request lock."""

    def setUp(self):
        """Create a DTU and socket doubles without making network connections."""
        self.dtu = DTU("test.invalid", timeout=0.01)
        self.request = Mock()
        self.response = object()
        self.reader = Mock(read=AsyncMock(return_value=b"response"))
        self.writer = Mock(drain=AsyncMock(), wait_closed=AsyncMock())
        self.connection = AsyncMock(return_value=(self.reader, self.writer))
        self.dtu.generate_message = Mock(return_value=b"request")
        self.dtu.parse_response = Mock(return_value=self.response)

    async def send(self):
        """Fail promptly if transport cleanup leaves the DTU request stuck."""
        return await asyncio.wait_for(
            self.dtu.async_send_request(b"\xa3\x11", self.request, Mock()), timeout=0.5
        )

    async def stall(self, *_args):
        """Simulate socket I/O that never completes on its own."""
        await asyncio.Event().wait()

    async def test_stalled_close_preserves_response_and_allows_next_request(self):
        """Abort stalled shutdown without discarding a response or holding the lock."""
        self.writer.wait_closed.side_effect = self.stall
        with patch("hoymiles_wifi.dtu.asyncio.open_connection", self.connection):
            self.assertIs(await self.send(), self.response)
            self.assertFalse(self.dtu.mutex.locked())
            self.writer.transport.abort.assert_called_once()
            self.dtu.last_request_time = 0
            self.writer.wait_closed.side_effect = None
            self.assertIs(await self.send(), self.response)
        self.assertEqual(self.connection.await_count, 2)
        self.assertFalse(self.dtu.mutex.locked())

    async def test_read_and_close_timeout(self):
        """A timed-out read with a stalled close still returns an offline result."""
        self.reader.read.side_effect = self.stall
        self.writer.wait_closed.side_effect = self.stall
        with patch("hoymiles_wifi.dtu.asyncio.open_connection", self.connection):
            self.assertIsNone(await self.send())
        self.assertIs(self.dtu.get_state(), NetworkState.Offline)
        self.assertFalse(self.dtu.mutex.locked())
        self.writer.transport.abort.assert_called_once()
        self.dtu.parse_response.assert_not_called()

    async def test_stalled_write(self):
        """Apply the connection timeout to backpressure during writes too."""
        self.writer.drain.side_effect = self.stall
        with patch("hoymiles_wifi.dtu.asyncio.open_connection", self.connection):
            self.assertIsNone(await self.send())
        self.assertIs(self.dtu.get_state(), NetworkState.Offline)
        self.assertFalse(self.dtu.mutex.locked())
        self.reader.read.assert_not_awaited()
        self.writer.close.assert_called_once()
        self.writer.wait_closed.assert_awaited_once()

    async def test_failed_connection(self):
        """Do not try to close an unassigned writer after connection failure."""
        self.connection.side_effect = OSError("connection failed")
        with (
            patch("hoymiles_wifi.dtu.asyncio.open_connection", self.connection),
            patch("hoymiles_wifi.dtu.logger.debug") as debug,
        ):
            self.assertIsNone(await self.send())
        self.assertIs(self.dtu.get_state(), NetworkState.Offline)
        self.assertFalse(self.dtu.mutex.locked())
        self.writer.close.assert_not_called()
        self.assertFalse(any("closing" in str(call) for call in debug.call_args_list))

    async def test_close_error_preserves_response(self):
        """Abort a failed shutdown and keep the already received reply."""
        self.writer.wait_closed.side_effect = OSError("connection reset")
        with patch("hoymiles_wifi.dtu.asyncio.open_connection", self.connection):
            self.assertIs(await self.send(), self.response)
        self.writer.transport.abort.assert_called_once()
        self.assertFalse(self.dtu.mutex.locked())

    async def test_normal_close(self):
        """Keep ordinary requests graceful without aborting their transport."""
        with patch("hoymiles_wifi.dtu.asyncio.open_connection", self.connection):
            self.assertIs(await self.send(), self.response)
        self.writer.close.assert_called_once()
        self.writer.wait_closed.assert_awaited_once()
        self.writer.transport.abort.assert_not_called()
        self.assertFalse(self.dtu.mutex.locked())
