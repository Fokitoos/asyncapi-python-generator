# AsyncAPI Python WebSocket Client Generator

A dynamic, offline-capable generator for creating Python WebSocket clients from AsyncAPI 3.0.0 specifications. This tool generates complete, production-ready Python clients with type safety, modern packaging, and code quality tools.

## ✨ Features

- 🚀 **AsyncAPI 3.0.0 Support** - Full support for the latest AsyncAPI specification
- ⚡ **Async/Await Support** - Modern async clients with `websockets` library (recommended)
- 🔄 **Sync Support** - Traditional threaded clients with `websocket-client` library  
- 🔄 **Dynamic Generation** - Automatically adapts to spec changes (new fields, enums, messages)
- 📦 **Modern Python Packaging** - Poetry and UV compatible with pyproject.toml
- 🎯 **Type Safety** - Generated dataclasses and enums for all schemas
- 🌐 **WebSocket Support** - Complete WebSocket client with SSL/TLS support
- 🛠️ **Code Quality** - Pre-configured Black, isort, and Flake8
- 🔒 **Offline Capable** - No network dependencies for generation
- 📝 **Documentation** - Auto-generated README and usage examples

## 🚀 Quick Start

### Generate Async Client (Recommended)

```bash
# Generate modern async client using websockets library
python generate_client.py examples/gpio-api.json --async -o my-async-client
cd my-async-client
poetry install  
python client.py
```

### Generate Sync Client

```bash
# Generate traditional sync client using websocket-client library  
python generate_client.py examples/gpio-api.json -o my-sync-client
cd my-sync-client
poetry install
python client.py
```

## 🔄 Async vs Sync Clients

| Feature | Async Client (`--async`) | Sync Client (default) |
|---------|--------------------------|------------------------|
| **Library** | `websockets>=11.0.0` | `websocket-client>=1.6.0` |
| **Style** | Modern async/await | Traditional threading |
| **Performance** | Better for high concurrency | Good for simple use cases |
| **Error Handling** | Native async error handling | Thread-based error handling |
| **Recommended For** | New projects, async codebases | Legacy compatibility |

### Example Async Usage

```python
import asyncio
from client import YourApiClient

async def main():
    client = YourApiClient()
    
    # Async message handler
    async def handle_message(data):
        print(f"Received: {data}")
        # Can perform async operations
        await asyncio.sleep(0.1)
    
    client.on_your_message(handle_message)
    
    # Connect and send
    if await client.connect():
        await client.send_your_message({"key": "value"})
        await client.wait_for_disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd asyncapi-python-generator

# Install dependencies (optional, for development)
pip install -r requirements.txt
```

### Basic Usage

```bash
# Generate a Python client from your AsyncAPI spec
python generate_client.py path/to/your/asyncapi.json

# Specify custom output directory
python generate_client.py path/to/your/asyncapi.json -o my-client

# Show help
python generate_client.py --help
```

### Example

```bash
# Using the provided example
python generate_client.py examples/gpio-api.json -o gpio-client
cd gpio-client
poetry install
python client.py
```

## 📁 Generated Client Structure

The generator creates a complete Python package:

```
generated-client/
├── client.py          # Main WebSocket client class
├── pyproject.toml     # Poetry/UV configuration
├── README.md          # Usage documentation
├── .flake8           # Linting configuration
└── examples/         # Usage examples (optional)
```

## 🔧 Generated Client Features

### WebSocket Client
- **Automatic connection management** with reconnection logic
- **SSL/TLS support** with certificate validation
- **Threading support** for non-blocking operations
- **Message routing** with type-safe handlers
- **Error handling** with custom error handlers

### Type Safety
- **Dataclasses** for all object schemas
- **Enums** for string schemas with allowed values
- **Type hints** throughout the codebase
- **Optional field support** with proper defaults

### Code Quality
- **Black formatting** (88 character line length)
- **isort import sorting** (black profile)
- **Flake8 linting** with reasonable rules
- **Poetry/UV packaging** for dependency management

## 📋 Requirements

- **Python 3.8+**
- **No external dependencies** for the generator itself
- **Generated clients require:**
  - `websocket-client` (WebSocket support)
  - `certifi` (SSL certificate handling)

## 🔄 Spec Changes Support

The generator dynamically adapts to your AsyncAPI specification:

| Change Type | Automatic Support |
|-------------|-------------------|
| New message types | ✅ Auto-generates send/receive methods |
| New schema fields | ✅ Updates dataclasses with new fields |
| New enum values | ✅ Adds enum constants |
| Field type changes | ✅ Updates type hints |
| Required/optional changes | ✅ Adjusts field defaults |
| New servers | ✅ Updates default connection URLs |

## 📖 Usage Examples

### Basic Client Usage

```python
from client import YourAPIClient, MessageType, DataClass

# Initialize client
client = YourAPIClient("wss://your-server.com")

# Register message handlers
def handle_message(data):
    print(f"Received: {data}")

client.on_your_message(handle_message)

# Connect and send messages
if client.connect():
    client.send_your_message({"field": "value"})
    
    # Keep connection alive
    import time
    time.sleep(10)
    
    client.disconnect()
```

### Advanced Usage with Type Safety

```python
from client import YourAPIClient, YourEnum, YourDataClass

client = YourAPIClient()

# Type-safe data creation
data = YourDataClass(
    required_field="value",
    enum_field=YourEnum.OPTION_A,
    optional_field=42
)

# Send typed message
client.send_message(data.__dict__)
```

## 🛠️ Development

### Running Tests

```bash
# Test with example specs
python test_generator.py

# Generate and test specific spec
python generate_client.py examples/gpio-api.json -o test-client
cd test-client
poetry install
poetry run python -c "import client; print('✅ Import successful')"
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
```

## 📁 Directory Structure

```
asyncapi-python-generator/
├── README.md                 # This file
├── generate_client.py        # Main generator script
├── requirements.txt          # Development dependencies
├── examples/                 # Example AsyncAPI specifications
│   ├── gpio-api.json        # GPIO interface example
│   └── sensor-api.json      # Multi-message example
├── templates/               # Template files (internal)
│   ├── client_template.py   # Client class template
│   ├── pyproject_template.toml
│   └── readme_template.md
└── tests/                   # Test files
    ├── test_generator.py    # Generator tests
    └── example_outputs/     # Expected outputs
```

## 🔍 Example Specifications

### Simple GPIO Interface

```json
{
  "asyncapi": "3.0.0",
  "info": {
    "title": "GPIO Interface API",
    "version": "1.0.0"
  },
  "channels": {
    "gpio": {
      "messages": {
        "GpioMessage": {
          "payload": { "$ref": "#/components/schemas/Gpio" }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "GpioStatus": {
        "type": "string",
        "enum": ["high", "low"]
      },
      "Gpio": {
        "type": "object",
        "properties": {
          "pin": { "type": "integer" },
          "status": { "$ref": "#/components/schemas/GpioStatus" }
        },
        "required": ["pin", "status"]
      }
    }
  }
}
```

### Generated Client Usage

```python
from client import GPIOInterfaceAPIClient, GpioStatus, Gpio

client = GPIOInterfaceAPIClient()

def handle_gpio(data):
    print(f"GPIO {data['payload']['pin']}: {data['payload']['status']}")

client.on_gpiomessage(handle_gpio)

if client.connect():
    client.send_gpiomessage({
        "pin": 18,
        "status": "high"
    })
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure code quality with `black`, `isort`, and `flake8`
5. Submit a pull request

## 📄 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## 🔗 Related Projects

- [AsyncAPI Specification](https://www.asyncapi.com/)
- [AsyncAPI Generator](https://github.com/asyncapi/generator)
- [WebSocket Client](https://pypi.org/project/websocket-client/)

## 📞 Support

- 📖 [Documentation](https://github.com/yourusername/asyncapi-python-generator)
- 🐛 [Issue Tracker](https://github.com/yourusername/asyncapi-python-generator/issues)
- 💬 [Discussions](https://github.com/yourusername/asyncapi-python-generator/discussions)