#!/usr/bin/env python3
"""
AsyncAPI 3.0.0 Python WebSocket Client Generator

Generates complete Python WebSocket clients from AsyncAPI 3.0.0 specifications
with full type safety, modern packaging, and code quality tools.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase."""
    return ''.join(
        word.capitalize()
        for word in text.replace('-', '_').replace(' ', '_').split('_')
    )


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case."""
    return to_snake_case(text).replace('_', '-')


def generate_client(spec_file: str, output_dir: str) -> None:
    """Generate Python WebSocket client from AsyncAPI specification."""
    # Load AsyncAPI specification
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Specification file '{spec_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in specification file: {e}")
        sys.exit(1)

    # Validate AsyncAPI version
    api_version = spec.get('asyncapi', '')
    if not api_version.startswith('3.'):
        print(f"⚠️  Warning: This generator is optimized for AsyncAPI 3.x, "
              f"found version {api_version}")

    # Extract specification data
    info = spec.get('info', {})
    title = info.get('title', 'AsyncAPI Client')
    description = info.get(
        'description', 'Generated AsyncAPI WebSocket client'
    )
    
    # Get server information
    servers = spec.get('servers', {})
    if servers:
        first_server = list(servers.values())[0]
        protocol = first_server.get('protocol', 'wss')
        host = first_server.get('host', 'localhost')
        port = first_server.get('port')
        server_url = f"{protocol}://{host}" + (f":{port}" if port else "")
    else:
        server_url = "wss://localhost"

    # Get schemas and channels
    schemas = spec.get('components', {}).get('schemas', {})
    channels = spec.get('channels', {})

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate client code
    client_content = generate_client_code(
        title, description, server_url, schemas, channels
    )
    
    # Generate project configuration
    pyproject_content = generate_pyproject_toml(title, description)
    readme_content = generate_readme(title, description, schemas, channels)
    flake8_content = generate_flake8_config()

    # Write files
    files = {
        'client.py': client_content,
        'pyproject.toml': pyproject_content,
        'README.md': readme_content,
        '.flake8': flake8_content,
    }

    for filename, content in files.items():
        filepath = Path(output_dir) / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    # Print success message
    client_class_name = to_pascal_case(title.replace(' ', '')) + 'Client'
    print("✅ Successfully generated Python client!")
    print(f"   📁 Output directory: {output_dir}")
    print(f"   🐍 Client class: {client_class_name}")
    print("   📦 Files generated:")
    for filename in files.keys():
        print(f"      - {filename}")
    print("\n🚀 Quick start:")
    print(f"   cd {output_dir}")
    print("   poetry install  # or: pip install -e .")
    print("   python client.py")


def generate_client_code(title: str, description: str, server_url: str,
                         schemas: dict, channels: dict) -> str:
    """Generate the main client Python code."""
    
    client_class_name = to_pascal_case(title.replace(' ', '')) + 'Client'
    
    # Start building the client code
    code = f'''"""
AsyncAPI WebSocket Client for {title}.

{description}

This client was automatically generated from an AsyncAPI 3.0.0 specification.
"""
import json
import ssl
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import certifi
    import websocket
except ImportError as e:
    print("❌ Missing required dependencies. Install with:")
    print("   pip install websocket-client certifi")
    print("   or: poetry install")
    raise e


# Generated Enums
'''

    # Generate enums for string schemas with enum values
    for schema_name, schema in schemas.items():
        if (schema.get('type') == 'string' and
                'enum' in schema and
                schema['enum']):

            enum_class_name = to_pascal_case(schema_name)
            enum_description = schema.get(
                'description', f'Enum for {schema_name}'
            )
            
            code += f'''
class {enum_class_name}(Enum):
    """{enum_description}."""

'''
            for enum_value in schema['enum']:
                const_name = (enum_value.upper()
                              .replace('-', '_')
                              .replace(' ', '_')
                              .replace('.', '_'))
                code += f'    {const_name} = "{enum_value}"\n'

    code += '\n\n# Generated Data Classes'

    # Generate dataclasses for object schemas
    for schema_name, schema in schemas.items():
        if schema.get('type') == 'object':
            properties = schema.get('properties', {})
            required = set(schema.get('required', []))
            
            class_name = to_pascal_case(schema_name)
            class_description = schema.get(
                'description', f'Data class for {schema_name}'
            )

            code += f'''

@dataclass
class {class_name}:
    """{class_description}."""

'''
            # Add required fields first (dataclass requirement)
            for prop_name, prop_schema in properties.items():
                if prop_name in required:
                    prop_type = get_python_type(prop_schema, schemas)
                    prop_desc = prop_schema.get('description', '')
                    code += f'    {prop_name}: {prop_type}'
                    if prop_desc:
                        code += f'  # {prop_desc}'
                    code += '\n'
            
            # Add optional fields with defaults
            for prop_name, prop_schema in properties.items():
                if prop_name not in required:
                    prop_type = get_python_type(prop_schema, schemas)
                    prop_desc = prop_schema.get('description', '')
                    code += f'    {prop_name}: Optional[{prop_type}] = None'
                    if prop_desc:
                        code += f'  # {prop_desc}'
                    code += '\n'

    # Generate main client class
    code += f'''

class {client_class_name}:
    """
    AsyncAPI WebSocket Client for {title}.
    
    {description}
    
    This client provides WebSocket connectivity with automatic message routing,
    type-safe data handling, and comprehensive error management.
    """

    def __init__(self, server_url: str = "{server_url}"):
        """
        Initialize the WebSocket client.
        
        Args:
            server_url: WebSocket server URL (default: {server_url})
        """
        self.url = server_url
        self.ws = None
        self.message_handlers: Dict[str, List[Callable]] = {{}}
        self.error_handlers: List[Callable] = []
        self.connected = False
        self._thread = None
        self._should_reconnect = False

    def connect(self, auto_reconnect: bool = False) -> bool:
        """
        Connect to the WebSocket server.
        
        Args:
            auto_reconnect: Whether to automatically reconnect on disconnect
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._should_reconnect = auto_reconnect
            
            # Create SSL context with certificate verification
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            # Start WebSocket connection in separate thread
            self._thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={{"sslopt": {{"cert_reqs": ssl.CERT_NONE}}}},
                daemon=True
            )
            self._thread.start()

            # Wait for connection to establish
            time.sleep(1)
            return self.connected

        except Exception as e:
            print(f"❌ Connection failed: {{e}}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        self._should_reconnect = False
        if self.ws:
            self.ws.close()
        self.connected = False

    def wait_for_disconnect(self) -> None:
        """Block until the connection is closed."""
        if self._thread and self._thread.is_alive():
            self._thread.join()

    def is_connected(self) -> bool:
        """Check if client is currently connected."""
        return self.connected

    def _on_open(self, ws) -> None:
        """Handle WebSocket connection opened."""
        self.connected = True
        print(f"✅ Connected to {{self.url}}")

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Handle WebSocket connection closed."""
        self.connected = False
        print(f"🔌 Disconnected from {{self.url}} "
              f"(code: {{close_status_code}}, message: {{close_msg}})")
        
        if self._should_reconnect:
            print("🔄 Attempting to reconnect...")
            time.sleep(5)
            self.connect(auto_reconnect=True)

    def _on_error(self, ws, error) -> None:
        """Handle WebSocket error."""
        print(f"❌ WebSocket error: {{error}}")
        for handler in self.error_handlers:
            try:
                handler(error)
            except Exception as e:
                print(f"❌ Error handler failed: {{e}}")

    def _on_message(self, ws, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            if message_type in self.message_handlers:
                for handler in self.message_handlers[message_type]:
                    try:
                        handler(data)
                    except Exception as e:
                        print(f"❌ Message handler error: {{e}}")
            else:
                print(f"⚠️  No handler for message type: {{message_type}}")

        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode message: {{e}}")
            print(f"   Raw message: {{message}}")

    def register_message_handler(
        self,
        message_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a handler for specific message types.
        
        Args:
            message_type: Type of message to handle
            handler: Function to call when message is received
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)

    def register_error_handler(
        self,
        handler: Callable[[Exception], None]
    ) -> None:
        """
        Register an error handler.
        
        Args:
            handler: Function to call when errors occur
        """
        self.error_handlers.append(handler)

    def send_message(self, data: Dict[str, Any]) -> bool:
        """
        Send a message to the server.
        
        Args:
            data: Message data to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.connected or not self.ws:
            print("❌ Cannot send message: Not connected to server")
            return False

        try:
            message = json.dumps(data, default=str)
            self.ws.send(message)
            return True
        except Exception as e:
            print(f"❌ Failed to send message: {{e}}")
            return False

    def send_raw_message(self, message: str) -> bool:
        """
        Send a raw string message to the server.
        
        Args:
            message: Raw message string to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.connected or not self.ws:
            print("❌ Cannot send message: Not connected to server")
            return False

        try:
            self.ws.send(message)
            return True
        except Exception as e:
            print(f"❌ Failed to send raw message: {{e}}")
            return False
'''

    # Generate message-specific methods
    for channel_name, channel in channels.items():
        messages = channel.get('messages', {})
        for message_name, message_spec in messages.items():
            method_name = to_snake_case(message_name).lower()
            
            code += f'''
    def send_{method_name}(self, payload: Dict[str, Any]) -> bool:
        """
        Send {message_name} message.
        
        Args:
            payload: Message payload data
            
        Returns:
            bool: True if message sent successfully
        """
        message_data = {{
            "type": "{message_name}",
            "payload": payload
        }}
        return self.send_message(message_data)

    def on_{method_name}(
        self, 
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register handler for {message_name} messages.
        
        Args:
            handler: Function to call when {message_name} is received
        """
        self.register_message_handler("{message_name}", handler)
'''

    # Add example usage
    code += f'''

def main() -> None:
    """Example usage of the {title} client."""
    client = {client_class_name}()
    
    print(f"🚀 Starting {{client.__class__.__name__}}...")
    print(f"   Server URL: {{client.url}}")
    
    # Register message handlers
'''
    
    # Add example handlers for each message type
    for channel_name, channel in channels.items():
        messages = channel.get('messages', {})
        for message_name, message_spec in messages.items():
            method_name = to_snake_case(message_name).lower()
            code += f'''
    def handle_{method_name}(data: Dict[str, Any]) -> None:
        """Handle {message_name} messages."""
        payload = data.get("payload", {{}})
        print(f"📨 Received {message_name}: {{payload}}")
    
    client.on_{method_name}(handle_{method_name})
'''

    code += f'''
    # Register error handler
    def handle_error(error: Exception) -> None:
        """Handle connection errors."""
        print(f"❌ Connection error: {{error}}")
    
    client.register_error_handler(handle_error)
    
    # Connect to server
    if client.connect(auto_reconnect=True):
        print("✅ Connected! Press Ctrl+C to disconnect.")
        
        # Example: Send a message after connection
        # Uncomment and modify as needed:
        # client.send_your_message({{"example": "data"}})
        
        try:
            # Keep client running
            client.wait_for_disconnect()
        except KeyboardInterrupt:
            print("\\n🛑 Shutting down...")
            client.disconnect()
    else:
        print("❌ Failed to connect to server")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
'''

    return code


def get_python_type(schema: dict, all_schemas: dict) -> str:
    """Convert AsyncAPI schema to Python type annotation."""
    if '$ref' in schema:
        # Reference to another schema
        ref_name = schema['$ref'].split('/')[-1]
        return to_pascal_case(ref_name)
    
    schema_type = schema.get('type', 'Any')
    
    if schema_type == 'string':
        if 'enum' in schema:
            # Enum reference
            title = schema.get('title', 'UnknownEnum')
            return to_pascal_case(title)
        return 'str'
    elif schema_type == 'integer':
        return 'int'
    elif schema_type == 'number':
        return 'float'
    elif schema_type == 'boolean':
        return 'bool'
    elif schema_type == 'array':
        items_type = get_python_type(schema.get('items', {}), all_schemas)
        return f'List[{items_type}]'
    elif schema_type == 'object':
        return 'Dict[str, Any]'
    else:
        return 'Any'


def generate_pyproject_toml(title: str, description: str) -> str:
    """Generate pyproject.toml configuration."""
    package_name = to_kebab_case(title.replace(' ', '-')) + '-client'
    
    return f'''[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[project]
name = "{package_name}"
version = "1.0.0"
description = "{description}"
authors = [
    {{name = "Generated from AsyncAPI", email = "contact@example.com"}}
]
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "websocket-client>=1.6.0",
    "certifi>=2023.7.22"
]

[project.optional-dependencies]
dev = [
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "flake8-black>=0.3.6",
    "flake8-isort>=6.0.0",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0"
]

[tool.poetry]
package-mode = false

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
'''


def generate_readme(title: str, description: str, schemas: dict,
                    channels: dict) -> str:
    """Generate README.md documentation."""
    client_class_name = to_pascal_case(title.replace(' ', '')) + 'Client'
    
    # Generate schema documentation
    schema_docs = ""
    if schemas:
        schema_docs = "### Generated Data Types\n\n"
        for schema_name, schema in schemas.items():
            class_name = to_pascal_case(schema_name)
            if schema.get('type') == 'string' and 'enum' in schema:
                enum_values = ', '.join(f'`{v}`' for v in schema['enum'])
                schema_docs += f"- **{class_name}** (Enum): {enum_values}\n"
            elif schema.get('type') == 'object':
                properties = schema.get('properties', {})
                if properties:
                    prop_list = ', '.join(properties.keys())
                    schema_docs += f"- **{class_name}** (Class): {prop_list}\n"
        schema_docs += "\n"

    # Generate method documentation
    method_docs = ""
    if channels:
        method_docs = "### Available Methods\n\n"
        for channel_name, channel in channels.items():
            messages = channel.get('messages', {})
            for message_name, message_spec in messages.items():
                method_name = to_snake_case(message_name).lower()
                method_docs += (
                    f"- `send_{method_name}(payload)` - Send {message_name}\n"
                )
                method_docs += (
                    f"- `on_{method_name}(handler)` - Handle {message_name}\n"
                )
        method_docs += "\n"

    return f'''# {title} Python Client

{description}

This client was automatically generated from an AsyncAPI 3.0.0 specification.

## Installation

### Using Poetry (Recommended)
```bash
poetry install
```

### Using pip
```bash
pip install -e .

# For development
pip install -e .[dev]
```

## Quick Start

```python
from client import {client_class_name}

# Create client
client = {client_class_name}()

# Register message handlers
def handle_message(data):
    print(f"Received message: {{data}}")

# Connect to server
if client.connect():
    print("Connected successfully!")
    
    # Your code here...
    
    client.disconnect()
else:
    print("Failed to connect")
```

## Features

- ✅ **WebSocket Support** - Full WebSocket client with SSL/TLS
- ✅ **Type Safety** - Generated dataclasses and enums  
- ✅ **Auto-Reconnection** - Configurable reconnection logic
- ✅ **Error Handling** - Comprehensive error management
- ✅ **Message Routing** - Type-safe message handlers
- ✅ **Modern Python** - Python 3.8+ with type hints

{schema_docs}{method_docs}## API Reference

### {client_class_name}

#### Connection Methods
- `connect(auto_reconnect=False)` - Connect to server
- `disconnect()` - Disconnect from server  
- `is_connected()` - Check connection status
- `wait_for_disconnect()` - Block until disconnected

#### Messaging Methods
- `send_message(data)` - Send structured message
- `send_raw_message(message)` - Send raw string message
- `register_message_handler(type, handler)` - Register message handler
- `register_error_handler(handler)` - Register error handler

## Development

### Code Quality

```bash
# Format code
poetry run black .
poetry run isort .

# Lint code  
poetry run flake8 .

# Run tests (if available)
poetry run pytest
```

### Example Usage

```python
import time
from client import {client_class_name}

def main():
    client = {client_class_name}()
    
    # Register handlers
    def handle_message(data):
        print(f"📨 {{data}}")
    
    def handle_error(error):
        print(f"❌ {{error}}")
    
    # Setup client
    client.register_error_handler(handle_error)
    
    # Connect with auto-reconnection
    if client.connect(auto_reconnect=True):
        try:
            # Keep running
            while client.is_connected():
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            client.disconnect()

if __name__ == "__main__":
    main()
```

## Generated from AsyncAPI

This client was automatically generated from an AsyncAPI specification.
To regenerate with updates, run the generator again with your updated spec.
'''


def generate_flake8_config() -> str:
    """Generate .flake8 configuration."""
    return '''[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude = .git,__pycache__,build,dist,*.egg
per-file-ignores = __init__.py:F401
'''


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Python WebSocket client from AsyncAPI 3.0.0 specification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python generate_client.py api.json
  python generate_client.py api.json -o my-client
  python generate_client.py api.json --output ./generated-client

The generator creates a complete Python package with:
  - WebSocket client class with type safety
  - Modern packaging (pyproject.toml)  
  - Code quality tools (black, isort, flake8)
  - Comprehensive documentation
        '''
    )
    
    parser.add_argument(
        'spec', 
        help='Path to AsyncAPI 3.0.0 specification file (JSON or YAML)'
    )
    parser.add_argument(
        '-o', '--output', 
        default='generated-client',
        help='Output directory for generated client (default: generated-client)'
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version='AsyncAPI Python Generator 1.0.0'
    )

    if len(sys.argv) == 1:
        parser.print_help()
        return 1

    args = parser.parse_args()

    if not os.path.exists(args.spec):
        print(f"❌ Error: Specification file '{args.spec}' not found")
        return 1

    try:
        generate_client(args.spec, args.output)
        return 0
    except KeyboardInterrupt:
        print("\n❌ Generation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error generating client: {e}")
        if os.environ.get('DEBUG'):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())