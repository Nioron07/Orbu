"""
Schema Introspection Service

Extracts parameter types and generates schemas from Acumatica service method signatures.
"""

import inspect
import logging
from typing import Any, Dict, List, Optional, get_type_hints, get_origin, get_args

logger = logging.getLogger(__name__)


class SchemaService:
    """Service for extracting and generating schemas from method signatures."""

    @staticmethod
    def get_method_signature(service_obj, method_name: str) -> Dict[str, Any]:
        """
        Extract method signature information including parameters and types.

        Args:
            service_obj: The Acumatica service object
            method_name: Name of the method to inspect

        Returns:
            Dict containing:
                - method_name: str
                - parameters: List of parameter definitions
                - has_return_type: bool
                - return_type: str (if available)
        """
        try:
            # First try to get signature from easy-acumatica registry
            signature_str = None
            if hasattr(service_obj, 'get_signature'):
                try:
                    signature_str = service_obj.get_signature(method_name)
                    logger.debug(f"Got signature from registry for {method_name}: {signature_str}")
                except (ValueError, AttributeError) as e:
                    logger.debug(f"No registry signature for {method_name}: {e}")

            # Parse the signature string if we got one
            if signature_str:
                return SchemaService._parse_signature_string(method_name, signature_str)

            # Fallback to inspect.signature (won't have type info for dynamic methods)
            method = getattr(service_obj, method_name)
            sig = inspect.signature(method)

            parameters = []
            for param_name, param in sig.parameters.items():
                # Skip 'self' parameter
                if param_name == 'self':
                    continue

                param_info = {
                    'name': param_name,
                    'required': param.default == inspect.Parameter.empty,
                    'default': None if param.default == inspect.Parameter.empty else str(param.default),
                    'type': SchemaService._extract_type_info(param.annotation),
                }

                parameters.append(param_info)

            # Extract return type if available
            return_annotation = sig.return_annotation
            return_type_info = None
            if return_annotation != inspect.Signature.empty:
                return_type_info = SchemaService._extract_type_info(return_annotation)

            return {
                'method_name': method_name,
                'parameters': parameters,
                'has_return_type': return_type_info is not None,
                'return_type': return_type_info,
            }

        except Exception as e:
            logger.error(f"Error extracting signature for {method_name}: {e}")
            return {
                'method_name': method_name,
                'parameters': [],
                'has_return_type': False,
                'return_type': None,
                'error': str(e)
            }

    @staticmethod
    def _parse_signature_string(method_name: str, signature_str: str) -> Dict[str, Any]:
        """
        Parse a signature string like "method_name(param1: type, param2: type = default) -> return_type"

        Args:
            method_name: Name of the method
            signature_str: Signature string to parse

        Returns:
            Dict with parsed signature information
        """
        import re

        parameters = []
        return_type_info = None

        try:
            # Extract parameters from signature: "method(param1: type, param2: type = default)"
            # Find content between parentheses
            param_match = re.search(r'\((.*?)\)', signature_str)
            if param_match:
                params_str = param_match.group(1).strip()
                if params_str:
                    # Split by comma, but be careful of nested types
                    param_parts = []
                    current_param = ""
                    bracket_depth = 0

                    for char in params_str:
                        if char in '[{(':
                            bracket_depth += 1
                        elif char in ']})':
                            bracket_depth -= 1
                        elif char == ',' and bracket_depth == 0:
                            param_parts.append(current_param.strip())
                            current_param = ""
                            continue
                        current_param += char

                    if current_param:
                        param_parts.append(current_param.strip())

                    # Parse each parameter
                    for param_str in param_parts:
                        param_str = param_str.strip()
                        if not param_str:
                            continue

                        # Check for default value
                        has_default = '=' in param_str
                        if has_default:
                            param_str, default_val = param_str.split('=', 1)
                            param_str = param_str.strip()
                            default_val = default_val.strip()
                        else:
                            default_val = None

                        # Split name and type
                        if ':' in param_str:
                            param_name, param_type = param_str.split(':', 1)
                            param_name = param_name.strip()
                            param_type = param_type.strip()
                        else:
                            param_name = param_str
                            param_type = 'str'  # Default to string if no type specified

                        # Convert Python type hints to JSON schema types
                        json_type = SchemaService._python_type_to_json_type(param_type)

                        parameters.append({
                            'name': param_name,
                            'required': not has_default,
                            'default': default_val,
                            'type': {'type': json_type, 'python_type': param_type}
                        })

            # Extract return type: "-> return_type"
            return_match = re.search(r'->\s*(.+?)$', signature_str)
            if return_match:
                return_type_str = return_match.group(1).strip()
                json_type = SchemaService._python_type_to_json_type(return_type_str)
                return_type_info = {'type': json_type, 'python_type': return_type_str}

        except Exception as e:
            logger.error(f"Error parsing signature string '{signature_str}': {e}")

        return {
            'method_name': method_name,
            'parameters': parameters,
            'has_return_type': return_type_info is not None,
            'return_type': return_type_info,
        }

    @staticmethod
    def _python_type_to_json_type(python_type: str) -> str:
        """Convert a Python type string to a JSON schema type."""
        # Handle Union types like "QueryOptions | None" or "str | None"
        if '|' in python_type:
            # Split by | and remove whitespace
            types = [t.strip() for t in python_type.split('|')]
            # Filter out None types
            non_none_types = [t for t in types if t.lower() not in ('none', 'nonetype')]

            # If we have one non-None type, use that (it's an Optional[Type])
            if len(non_none_types) == 1:
                python_type = non_none_types[0]
            elif len(non_none_types) == 0:
                return 'null'
            # If multiple non-None types, just use the first one for now
            else:
                python_type = non_none_types[0]

        python_type_lower = python_type.lower()

        if 'str' in python_type_lower or 'string' in python_type_lower:
            return 'string'
        elif 'int' in python_type_lower or 'integer' in python_type_lower:
            return 'integer'
        elif 'float' in python_type_lower or 'number' in python_type_lower or 'decimal' in python_type_lower:
            return 'number'
        elif 'bool' in python_type_lower or 'boolean' in python_type_lower:
            return 'boolean'
        elif 'list' in python_type_lower or 'array' in python_type_lower:
            return 'array'
        elif 'dict' in python_type_lower or 'object' in python_type_lower:
            return 'object'
        elif 'none' in python_type_lower or 'null' in python_type_lower:
            return 'null'
        else:
            return 'object'  # Default to object for complex types

    @staticmethod
    def _extract_type_info(annotation) -> Dict[str, Any]:
        """
        Extract type information from a parameter annotation.

        Args:
            annotation: The type annotation

        Returns:
            Dict with type information
        """
        if annotation == inspect.Parameter.empty:
            return {'type': 'any', 'python_type': 'Any'}

        # Handle string annotations
        if isinstance(annotation, str):
            return {'type': 'string', 'python_type': annotation}

        # Get the type name
        type_name = getattr(annotation, '__name__', str(annotation))

        # Check for Optional types (Union with None)
        origin = get_origin(annotation)
        if origin is not None:
            args = get_args(annotation)

            # Handle Union types (including Optional)
            if origin.__name__ == 'Union':
                # Check if it's Optional (Union with None)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if len(non_none_types) == 1 and type(None) in args:
                    # This is Optional[SomeType]
                    inner_type = non_none_types[0]
                    inner_info = SchemaService._extract_type_info(inner_type)
                    return {
                        'type': inner_info['type'],
                        'python_type': inner_info['python_type'],
                        'optional': True
                    }
                else:
                    # Multiple types in union
                    return {
                        'type': 'union',
                        'python_type': str(annotation),
                        'types': [SchemaService._extract_type_info(arg) for arg in args]
                    }

            # Handle List, Dict, etc.
            return {
                'type': origin.__name__.lower(),
                'python_type': str(annotation),
                'args': [SchemaService._extract_type_info(arg) for arg in args]
            }

        # Map Python types to JSON schema types
        type_mapping = {
            'str': 'string',
            'int': 'integer',
            'float': 'number',
            'bool': 'boolean',
            'dict': 'object',
            'Dict': 'object',
            'list': 'array',
            'List': 'array',
            'None': 'null',
            'NoneType': 'null',
        }

        json_type = type_mapping.get(type_name, 'object')

        return {
            'type': json_type,
            'python_type': type_name
        }

    @staticmethod
    def generate_request_schema(method_signature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a JSON schema for the request body based on method signature.

        Args:
            method_signature: Output from get_method_signature()

        Returns:
            JSON schema dict
        """
        properties = {}
        required = []

        for param in method_signature.get('parameters', []):
            param_schema = {
                'type': param['type'].get('type', 'any'),
            }

            # Add description if available
            if param['type'].get('python_type'):
                param_schema['description'] = f"Type: {param['type']['python_type']}"

            # Handle default values
            if not param['required'] and param['default']:
                param_schema['default'] = param['default']

            properties[param['name']] = param_schema

            if param['required']:
                required.append(param['name'])

        schema = {
            'type': 'object',
            'properties': properties,
        }

        if required:
            schema['required'] = required

        return schema

    @staticmethod
    def generate_response_schema(method_signature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a JSON schema for the expected response based on return type.

        Args:
            method_signature: Output from get_method_signature()

        Returns:
            JSON schema dict for response
        """
        method_name = method_signature.get('method_name', '').lower()

        # Determine data schema based on return type
        data_schema = {'type': 'object'}

        if method_signature.get('has_return_type'):
            return_type = method_signature.get('return_type', {})
            python_type = return_type.get('python_type', '')
            json_type = return_type.get('type', 'object')

            # Handle different return types
            if 'list' in python_type.lower() or json_type == 'array':
                # Methods that return lists (get_list, query, etc.)
                # Extract the inner type from list[Type] notation
                inner_type = python_type
                if '[' in python_type and ']' in python_type:
                    inner_type = python_type.split('[')[1].split(']')[0]

                data_schema = {
                    'type': 'array',
                    'items': {'type': 'object'},
                    'description': f'Array of {inner_type} objects'
                }
            elif json_type == 'boolean':
                # Delete/update methods that return success status
                data_schema = {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string'},
                        'message': {'type': 'string'}
                    },
                    'description': f'Operation status - Type: {python_type}'
                }
            elif json_type == 'string':
                # Methods returning strings (IDs, messages, etc.)
                data_schema = {
                    'type': 'string',
                    'description': f'Type: {python_type}'
                }
            elif json_type == 'integer' or json_type == 'number':
                # Methods returning numbers
                data_schema = {
                    'type': json_type,
                    'description': f'Type: {python_type}'
                }
            elif 'dict' in python_type.lower() or json_type == 'object':
                # Methods returning single objects (get, get_by_id, etc.)
                data_schema = {
                    'type': 'object',
                    'description': f'Single object - Type: {python_type}'
                }
            else:
                # Default to object with type info
                data_schema = {
                    'type': json_type,
                    'description': f'Type: {python_type}'
                }
        else:
            # No return type specified - infer from method name
            if any(keyword in method_name for keyword in ['list', 'query', 'search', 'get_all']):
                data_schema = {
                    'type': 'array',
                    'items': {'type': 'object'},
                    'description': 'Array of objects'
                }
            elif any(keyword in method_name for keyword in ['delete', 'remove', 'update', 'put']):
                data_schema = {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string'},
                        'message': {'type': 'string'}
                    },
                    'description': 'Operation status'
                }

        # Standard response wrapper
        schema = {
            'type': 'object',
            'properties': {
                'success': {
                    'type': 'boolean',
                    'description': 'Indicates if the request was successful'
                },
                'data': data_schema,
                'meta': {
                    'type': 'object',
                    'description': 'Metadata about the request execution',
                    'properties': {
                        'duration_ms': {'type': 'integer'},
                        'endpoint_id': {'type': 'string'},
                        'executed_at': {'type': 'string', 'format': 'date-time'}
                    }
                }
            },
            'required': ['success', 'data']
        }

        return schema

    @staticmethod
    def generate_example_request(method_signature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an example request body based on the method signature.

        Args:
            method_signature: Output from get_method_signature()

        Returns:
            Example request dict
        """
        example = {}

        for param in method_signature.get('parameters', []):
            param_type = param['type'].get('type', 'string')

            # Generate example values based on type
            if param_type == 'string':
                example[param['name']] = f"example_{param['name']}"
            elif param_type == 'integer':
                example[param['name']] = 0
            elif param_type == 'number':
                example[param['name']] = 0.0
            elif param_type == 'boolean':
                example[param['name']] = True
            elif param_type == 'array':
                example[param['name']] = []
            elif param_type == 'object':
                example[param['name']] = {}
            else:
                example[param['name']] = None

            # Use default value if available
            if not param['required'] and param['default'] and param['default'] != 'None':
                example[param['name']] = param['default']

        return example

    @staticmethod
    def get_complete_schema(service_obj, method_name: str) -> Dict[str, Any]:
        """
        Get complete schema information for a method including request, response, and examples.

        Args:
            service_obj: The Acumatica service object
            method_name: Name of the method

        Returns:
            Complete schema dict
        """
        signature = SchemaService.get_method_signature(service_obj, method_name)

        return {
            'method_name': method_name,
            'signature': signature,
            'request_schema': SchemaService.generate_request_schema(signature),
            'response_schema': SchemaService.generate_response_schema(signature),
            'example_request': SchemaService.generate_example_request(signature),
        }
