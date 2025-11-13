# Contributing to AsyncAPI Python Generator

We welcome contributions! This project aims to provide a robust, offline-capable generator for Python WebSocket clients from AsyncAPI 3.0.0 specifications.

## Development Setup

### Prerequisites
- Python 3.8+
- Poetry (recommended) or pip

### Quick Start
```bash
# Clone the repository
git clone <your-repo-url>
cd asyncapi-python-generator

# Install dependencies
poetry install
# OR
pip install -r requirements-dev.txt

# Run the generator
python generate_client.py examples/gpio-api.json -o test-output
```

## Project Structure

```
asyncapi-python-generator/
├── generate_client.py          # Main generator script
├── README.md                   # Project documentation
├── LICENSE                     # MIT license
├── requirements-dev.txt        # Development dependencies
├── CONTRIBUTING.md             # This file
└── examples/                   # Example AsyncAPI specifications
    ├── gpio-api.json          # Simple GPIO interface
    └── iot-device-manager.json # Complex IoT example
```

## Code Quality

We maintain high code quality standards:

### Formatting
```bash
# Format code with black
black generate_client.py

# Sort imports with isort  
isort generate_client.py
```

### Linting
```bash
# Check code style
flake8 generate_client.py
```

### Configuration
- **Line length**: 79 characters (flake8 standard)
- **Import sorting**: black-compatible profile
- **Type hints**: Required for all public functions

## Testing Locally

### Basic Test
```bash
# Generate client from GPIO example
python generate_client.py examples/gpio-api.json -o test-gpio

# Check generated files
cd test-gpio
python client.py --help
```

### Advanced Test
```bash
# Generate from complex IoT example
python generate_client.py examples/iot-device-manager.json -o test-iot

# Verify code quality
cd test-iot
flake8 client.py
black --check client.py
isort --check-only client.py
```

## Generator Features

### Supported AsyncAPI 3.0.0 Features
- ✅ **Schemas**: Object types, enums, primitive types
- ✅ **Channels**: WebSocket channels with parameters  
- ✅ **Messages**: Bidirectional message definitions
- ✅ **Servers**: Multiple server configurations
- ✅ **References**: $ref resolution within components

### Generated Client Features
- ✅ **Type Safety**: Dataclasses for all object schemas
- ✅ **Enums**: Python enums for string enums
- ✅ **WebSocket**: Full WebSocket client with SSL/TLS
- ✅ **Reconnection**: Configurable auto-reconnection
- ✅ **Error Handling**: Comprehensive error management
- ✅ **Modern Packaging**: pyproject.toml, Poetry/uv compatible

## Extending the Generator

### Adding New Schema Types
```python
def get_python_type(schema: dict, all_schemas: dict) -> str:
    # Add support for new AsyncAPI schema types
    if schema_type == 'your_new_type':
        return 'YourPythonType'
```

### Adding Client Features
```python
def generate_client_code(...) -> str:
    # Add new methods to generated client class
    code += '''
    def your_new_method(self):
        """Your new client functionality."""
        pass
    '''
```

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Make** your changes with proper tests
4. **Ensure** code quality: `black .`, `isort .`, `flake8 .`
5. **Test** with example files
6. **Commit** with clear messages
7. **Push** and create a pull request

## Reporting Issues

### Bug Reports
Please include:
- Python version
- AsyncAPI specification that fails
- Error messages
- Expected vs actual behavior

### Feature Requests
Please describe:
- Use case and motivation
- Proposed API or behavior
- AsyncAPI features that need support

## AsyncAPI Version Support

- **Primary**: AsyncAPI 3.0.0 (full support)
- **Secondary**: AsyncAPI 2.x (basic compatibility)
- **Future**: AsyncAPI 3.1+ (planned)

The generator is optimized for AsyncAPI 3.0.0 and focuses on WebSocket protocol support.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.