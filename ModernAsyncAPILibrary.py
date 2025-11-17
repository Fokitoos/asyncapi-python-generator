"""
Modern AsyncAPI Robot Framework Library (Robot Framework 6.1+)

This library is directly compatible with the generated PhobosgpiointerfaceapiClient
and takes advantage of Robot Framework 6.1+ native async keyword support.

For Robot Framework 6.1+, async keywords are supported natively, eliminating the
need for complex event loop threading patterns.
"""

import asyncio
import sys
import os
from typing import Any, Dict, List, Optional
from robot.api.deco import keyword, library
from robot.api import logger

# Import the generated AsyncAPI client
# Adjust path as needed for your setup
sys.path.append(os.path.join(os.path.dirname(__file__), "my-client-ena"))
from client import PhobosgpiointerfaceapiClient


@library(scope="TEST")
class ModernAsyncAPILibrary:
    """
    Modern AsyncAPI Robot Framework Library using native async support.

    Requires Robot Framework 6.1 or later for async keyword support.

    This library provides direct async keywords that Robot Framework
    can execute natively without manual event loop management.
    """

    def __init__(self):
        """Initialize the modern AsyncAPI library."""
        self.client = None
        self.received_messages = []
        self.last_error = None
        self._client_class = None
        self._message_handlers = {}

    @keyword
    async def initialize_gpio_client(self, server_url: str = "wss://127.0.0.1"):
        """
        Initialize the Phobos GPIO interface API WebSocket client.

        This is an async keyword that Robot Framework 6.1+ can execute directly.
        Uses the generated PhobosgpiointerfaceapiClient directly.

        Args:
            server_url: WebSocket server URL (default matches client default)

        Example:
            | Initialize GPIO Client | wss://127.0.0.1 |
        """
        self.client = PhobosgpiointerfaceapiClient(server_url)

        # Set up message handlers
        await self._setup_message_handlers()

        logger.info(f"GPIO AsyncAPI client initialized for {server_url}")

    async def _setup_message_handlers(self):
        """Set up message and error handlers for the client."""

        # Generic message handler
        async def message_collector(data):
            self.received_messages.append(data)
            logger.info(f"Received message: {data}")

        # Error handler
        async def error_handler(error):
            self.last_error = str(error)
            logger.error(f"Client error: {error}")

        # Register handlers if client supports them
        if hasattr(self.client, "register_error_handler"):
            self.client.register_error_handler(error_handler)

        # Auto-register message handlers based on client methods
        for attr_name in dir(self.client):
            if attr_name.startswith("on_"):
                try:
                    handler_method = getattr(self.client, attr_name)
                    if callable(handler_method):
                        handler_method(message_collector)
                        logger.debug(f"Registered handler: {attr_name}")
                except Exception as e:
                    logger.debug(f"Could not register handler {attr_name}: {e}")

    @keyword
    async def connect_to_websocket_server(
        self, auto_reconnect: bool = False, timeout: int = 30
    ):
        """
        Connect to WebSocket server asynchronously.

        Args:
            auto_reconnect: Enable auto-reconnect
            timeout: Connection timeout in seconds

        Example:
            | Connect To WebSocket Server | auto_reconnect=${True} | timeout=30 |
        """
        if not self.client:
            raise RuntimeError(
                "Client not initialized. Call 'Initialize AsyncAPI Client' first."
            )

        try:
            # Use asyncio.wait_for for timeout handling
            connected = await asyncio.wait_for(
                self.client.connect(auto_reconnect=auto_reconnect), timeout=timeout
            )

            if connected:
                logger.info("Successfully connected to WebSocket server")
            else:
                raise AssertionError("Failed to connect to WebSocket server")

        except asyncio.TimeoutError:
            raise AssertionError(f"Connection timed out after {timeout} seconds")

    @keyword
    async def disconnect_from_websocket_server(self):
        """
        Disconnect from WebSocket server asynchronously.

        Example:
            | Disconnect From WebSocket Server |
        """
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from WebSocket server")

    @keyword
    async def send_gpio_message(self, payload: Dict[str, Any]):
        """
        Send a GPIO message to the WebSocket server asynchronously.

        Args:
            payload: GPIO message payload (dictionary)

        Example:
            | ${payload}= | Create Dictionary | status=high |
            | Send GPIO Message | ${payload} |
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        success = await self.client.send_gpio_message(payload)

        if not success:
            raise AssertionError("Failed to send GPIO message")

        logger.info(f"Sent GPIO message with payload: {payload}")

    @keyword
    async def send_raw_message(self, message: str):
        """
        Send a raw string message to the WebSocket server.

        Args:
            message: Raw message string

        Example:
            | Send Raw Message | {"type": "GpioMessage", "payload": {"status": "high"}} |
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        success = await self.client.send_raw_message(message)

        if not success:
            raise AssertionError("Failed to send raw message")

        logger.info(f"Sent raw message: {message}")

    @keyword
    async def send_custom_message(self, data: Dict[str, Any]):
        """
        Send a custom message using the generic send_message method.

        Args:
            data: Complete message data (including type and payload)

        Example:
            | ${data}= | Create Dictionary | type=GpioMessage |
            | Set To Dictionary | ${data} | payload | {"status": "high"} |
            | Send Custom Message | ${data} |
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        success = await self.client.send_message(data)

        if not success:
            raise AssertionError("Failed to send custom message")

        logger.info(f"Sent custom message: {data}")

    @keyword
    async def wait_for_websocket_message(
        self, message_type: str, timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for specific message type asynchronously.

        Args:
            message_type: Expected message type
            timeout: Timeout in seconds

        Returns:
            Dict containing the received message

        Example:
            | ${message}= | Wait For WebSocket Message | GpioAck | timeout=15 |
        """
        try:
            return await asyncio.wait_for(
                self._wait_for_message_async(message_type), timeout=timeout
            )
        except asyncio.TimeoutError:
            raise AssertionError(
                f"Message '{message_type}' not received within {timeout} seconds"
            )

    async def _wait_for_message_async(self, message_type: str) -> Dict[str, Any]:
        """Internal async method to wait for a message."""
        while True:
            # Check existing messages
            for i, msg in enumerate(self.received_messages):
                if msg.get("type") == message_type:
                    found_message = self.received_messages.pop(i)
                    logger.info(f"Received expected message: {message_type}")
                    return found_message

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

    @keyword
    async def wait_for_websocket_message_with_payload(
        self, message_type: str, payload_filter: Dict[str, Any], timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for message with specific payload content asynchronously.

        Args:
            message_type: Expected message type
            payload_filter: Dictionary of payload fields to match
            timeout: Timeout in seconds

        Returns:
            Dict containing the received message

        Example:
            | ${filter}= | Create Dictionary | pin=1 | status=high |
            | ${message}= | Wait For WebSocket Message With Payload | GpioMessage | ${filter} |
        """
        try:
            return await asyncio.wait_for(
                self._wait_for_message_with_payload_async(message_type, payload_filter),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise AssertionError(
                f"Message '{message_type}' with payload {payload_filter} not received within {timeout} seconds"
            )

    async def _wait_for_message_with_payload_async(
        self, message_type: str, payload_filter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Internal async method to wait for a message with specific payload."""
        while True:
            for i, msg in enumerate(self.received_messages):
                if msg.get("type") == message_type:
                    msg_payload = msg.get("payload", {})
                    # Check if all filter fields match
                    if all(msg_payload.get(k) == v for k, v in payload_filter.items()):
                        found_message = self.received_messages.pop(i)
                        logger.info(
                            f"Received expected message: {message_type} with matching payload"
                        )
                        return found_message

            await asyncio.sleep(0.1)

    @keyword
    def clear_received_messages(self):
        """
        Clear the received messages buffer.

        Example:
            | Clear Received Messages |
        """
        self.received_messages.clear()
        logger.info("Cleared received messages buffer")

    @keyword
    def should_be_connected(self):
        """
        Verify client is connected.

        Example:
            | Should Be Connected |
        """
        if not self.client or not self.client.is_connected():
            raise AssertionError("Client is not connected to WebSocket server")

    @keyword
    def should_be_disconnected(self):
        """
        Verify client is disconnected.

        Example:
            | Should Be Disconnected |
        """
        if self.client and self.client.is_connected():
            raise AssertionError("Client is still connected to WebSocket server")

    @keyword
    def get_message_count(self) -> int:
        """
        Get current number of received messages.

        Returns:
            Number of messages in buffer

        Example:
            | ${count}= | Get Message Count |
        """
        return len(self.received_messages)

    @keyword
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """
        Get all messages of specific type.

        Args:
            message_type: Message type to filter

        Returns:
            List of matching messages

        Example:
            | ${gpio_messages}= | Get Messages By Type | GpioMessage |
        """
        matching_messages = [
            msg for msg in self.received_messages if msg.get("type") == message_type
        ]
        logger.info(f"Found {len(matching_messages)} messages of type {message_type}")
        return matching_messages

    @keyword
    async def wait_for_multiple_websocket_messages(
        self, expected_count: int, timeout: int = 10
    ):
        """
        Wait for multiple messages to arrive asynchronously.

        Args:
            expected_count: Expected number of messages
            timeout: Timeout in seconds

        Example:
            | Wait For Multiple WebSocket Messages | 3 | timeout=15 |
        """
        initial_count = len(self.received_messages)

        try:
            await asyncio.wait_for(
                self._wait_for_message_count_async(initial_count + expected_count),
                timeout=timeout,
            )
            logger.info(f"Received {expected_count} messages as expected")
        except asyncio.TimeoutError:
            actual_received = len(self.received_messages) - initial_count
            raise AssertionError(
                f"Expected {expected_count} messages, got {actual_received} within {timeout} seconds"
            )

    async def _wait_for_message_count_async(self, target_count: int):
        """Internal async method to wait for specific message count."""
        while len(self.received_messages) < target_count:
            await asyncio.sleep(0.1)

    @keyword
    def get_last_error(self) -> Optional[str]:
        """
        Get the last error that occurred.

        Returns:
            Last error message or None

        Example:
            | ${error}= | Get Last Error |
            | Should Be Equal | ${error} | ${None} |
        """
        return self.last_error

    @keyword
    def clear_last_error(self):
        """
        Clear the last error.

        Example:
            | Clear Last Error |
        """
        self.last_error = None
        logger.info("Cleared last error")

    @keyword
    async def send_gpio_high(self):
        """
        Send GPIO HIGH command (convenience method).

        Example:
            | Send GPIO High |
        """
        await self.send_gpio_message({"status": "high"})

    @keyword
    async def send_gpio_low(self):
        """
        Send GPIO LOW command (convenience method).

        Example:
            | Send GPIO Low |
        """
        await self.send_gpio_message({"status": "low"})

    @keyword
    async def wait_for_gpio_message(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Wait for any GPIO message (convenience method).

        Args:
            timeout: Timeout in seconds

        Returns:
            Dict containing the received GPIO message

        Example:
            | ${message}= | Wait For GPIO Message | timeout=15 |
        """
        return await self.wait_for_websocket_message("GpioMessage", timeout)

    @keyword
    async def wait_for_gpio_status(self, expected_status: str, timeout: int = 10):
        """
        Wait for GPIO message with specific status.

        Args:
            expected_status: Expected GPIO status ('high' or 'low')
            timeout: Timeout in seconds

        Example:
            | Wait For GPIO Status | high | timeout=10 |
        """
        if expected_status not in ["high", "low"]:
            raise ValueError(f"Invalid GPIO status: {expected_status}")

        payload_filter = {"status": expected_status}
        message = await self.wait_for_websocket_message_with_payload(
            "GpioMessage", payload_filter, timeout
        )
        logger.info(f"Received GPIO status: {expected_status}")
        return message

    @keyword
    def get_gpio_messages(self) -> List[Dict[str, Any]]:
        """
        Get all GPIO messages from buffer (convenience method).

        Returns:
            List of GPIO messages

        Example:
            | ${gpio_msgs}= | Get GPIO Messages |
        """
        return self.get_messages_by_type("GpioMessage")

    @keyword
    async def cleanup_asyncapi_client(self):
        """
        Clean up client resources asynchronously.

        This keyword should be called in test teardown.

        Example:
            | [Teardown] | Cleanup AsyncAPI Client |
        """
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warn(f"Error during client cleanup: {e}")

        # Reset state
        self.client = None
        self.received_messages.clear()
        self.last_error = None

        logger.info("GPIO AsyncAPI client cleaned up")


# Example Robot Framework test using modern async approach:
"""
*** Settings ***
Library    ModernAsyncAPILibrary.py

*** Variables ***
${GPIO_SERVER_URL}    wss://127.0.0.1

*** Test Cases ***
GPIO WebSocket Connection Test
    [Documentation]    Test GPIO client connection using RF 6.1+ async support
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server    auto_reconnect=${True}
    Should Be Connected
    
    [Teardown]    Cleanup AsyncAPI Client

GPIO Message Test
    [Documentation]    Test GPIO message sending and receiving with convenience methods
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Should Be Connected
    
    Clear Received Messages
    
    # Send GPIO HIGH command (convenience method)
    Send GPIO High
    
    # Wait for specific GPIO status
    Wait For GPIO Status    high    timeout=10
    
    # Send GPIO LOW command (convenience method) 
    Send GPIO Low
    
    # Wait for GPIO message (any GPIO message)
    ${message}=    Wait For GPIO Message    timeout=10
    
    # Verify we received the LOW status
    ${payload}=    Get From Dictionary    ${message}    payload
    Should Be Equal    ${payload['status']}    low
    
    [Teardown]    Cleanup AsyncAPI Client

GPIO Raw Message Test
    [Documentation]    Test sending raw GPIO messages
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    
    # Send raw JSON message
    Send Raw Message    {"type": "GpioMessage", "payload": {"status": "high"}}
    
    # Send custom structured message
    ${data}=    Create Dictionary    type=GpioMessage
    ${payload}=    Create Dictionary    status=low
    Set To Dictionary    ${data}    payload    ${payload}
    Send Custom Message    ${data}
    
    [Teardown]    Cleanup AsyncAPI Client

GPIO Error Handling Test
    [Documentation]    Test GPIO client error handling
    
    # Try connecting to invalid server
    Initialize GPIO Client    wss://invalid-server:9999
    
    Run Keyword And Expect Error
    ...    Connection timed out after * seconds
    ...    Connect To WebSocket Server    timeout=5
    
    [Teardown]    Cleanup AsyncAPI Client
"""
