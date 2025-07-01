# Canvas Editor Code Evaluation Report
======================================================================

## Code Statistics
- Total Functions: 266
- Total Classes: 60
- Total Imports: 17
- Async Functions: 6
- Try/Except Blocks: 6

## Issues Summary
Total Issues Found: 94

### Critical Issues
- parse_errors: 11

### Code Quality Issues
- missing_return_type: 17
- missing_param_type: 11
- missing_docstring: 13
- async_without_await: 5
- complex_lambdas: 6

## Code Patterns
- magic_numbers: 27
- error_without_logging: 1

## Detailed Issues

### Missing Init
- {'file': 'src/managers/action_creators.py', 'class': 'ActionCreators'}
- {'file': 'src/managers/project_enhanced.py', 'class': 'ProjectCreationError'}
- {'file': 'src/managers/project_enhanced.py', 'class': 'ProjectImportError'}
- {'file': 'src/managers/project_enhanced.py', 'class': 'ProjectIOError'}
- {'file': 'src/managers/spatial_index.py', 'class': 'BoundingBox'}
  ... and 25 more

### Parse Errors
- {'file': 'src/managers/enhanced_state.py', 'error': "'Import' object has no attribute 'asname'"}
- {'file': 'src/managers/history_manager.py', 'error': "'Import' object has no attribute 'asname'"}
- {'file': 'src/managers/project.py', 'error': "'Import' object has no attribute 'asname'"}
- {'file': 'src/managers/project_enhanced.py', 'error': "'Import' object has no attribute 'asname'"}
- {'file': 'src/managers/project_state_integrated.py', 'error': "'Import' object has no attribute 'asname'"}
  ... and 6 more

### Missing Return Type
- {'file': 'src/managers/history_middleware.py', 'function': 'cleanup_cache', 'line': 79}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_component_tree', 'line': 239}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_selection_integrity', 'line': 255}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_project_integrity', 'line': 264}
- {'file': 'src/managers/history_middleware.py', 'function': '_deep_validate_state', 'line': 272}
  ... and 12 more

### Missing Param Type
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_component_tree', 'param': 'components', 'line': 239}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_component_tree', 'param': 'errors', 'line': 239}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_selection_integrity', 'param': 'selection', 'line': 255}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_selection_integrity', 'param': 'components', 'line': 255}
- {'file': 'src/managers/history_middleware.py', 'function': '_validate_selection_integrity', 'param': 'errors', 'line': 255}
  ... and 6 more

### Async Without Await
- {'file': 'src/managers/history_middleware.py', 'function': 'before_action', 'line': 27}
- {'file': 'src/managers/history_middleware.py', 'function': 'before_action', 'line': 118}
- {'file': 'src/managers/history_middleware.py', 'function': 'after_action', 'line': 159}
- {'file': 'src/managers/history_middleware.py', 'function': 'before_action', 'line': 192}
- {'file': 'src/managers/history_middleware.py', 'function': 'after_action', 'line': 200}

### Missing Docstring
- {'file': 'src/managers/history_middleware.py', 'type': 'FunctionDef', 'name': '__init__', 'line': 22}
- {'file': 'src/managers/history_middleware.py', 'type': 'FunctionDef', 'name': '__init__', 'line': 92}
- {'file': 'src/managers/history_middleware.py', 'type': 'FunctionDef', 'name': '__init__', 'line': 187}
- {'file': 'src/managers/history_middleware.py', 'type': 'FunctionDef', 'name': 'check_component_cycles', 'line': 277}
- {'file': 'src/managers/spatial_index.py', 'type': 'FunctionDef', 'name': 'left', 'line': 23}
  ... and 8 more

### Long Lines
- {'file': 'src/managers/spatial_index.py', 'line': 190, 'length': 122}

### Complex Lambdas
- {'file': 'src/managers/state_synchronizer.py', 'line': 83}
- {'file': 'src/managers/state_synchronizer.py', 'line': 121}
- {'file': 'src/managers/state_synchronizer.py', 'line': 123}
- {'file': 'src/managers/state_synchronizer.py', 'line': 134}
- {'file': 'src/managers/state_synchronizer.py', 'line': 144}
  ... and 1 more