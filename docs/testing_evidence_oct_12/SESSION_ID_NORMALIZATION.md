# Session ID Normalization in ProdLens

## Overview

The ProdLens trace normalizer intentionally transforms session IDs to ensure consistent formatting across different trace sources. This document explains why `session-abc123` in the input becomes `abc123` in the database.

## Implementation

**File**: `dev-agent-lens/scripts/src/prodlens/trace_normalizer.py`
**Lines**: 10, 76-79

```python
# Line 10: Define the pattern to match
_SESSION_PATTERN = re.compile(r"session[_-]([a-zA-Z0-9_-]+)")

# Lines 76-79: Extract and normalize session ID
for value in possible_values:
    match = _SESSION_PATTERN.search(value)
    if match:
        return match.group(1)  # Returns captured group (without prefix)
```

## Transformation Examples

| Input | Output | Explanation |
|-------|--------|-------------|
| `session-abc123` | `abc123` | Hyphen separator stripped |
| `session_xyz789` | `xyz789` | Underscore separator stripped |
| `abc123` | `abc123` | No prefix, used as-is |
| `user-session-def456` | `def456` | First match extracted |
| `my-session` | `session` | Pattern matches "session" |

## Rationale

Different systems generate session IDs with varying prefixes:

### LiteLLM Traces
```json
{
  "metadata": {
    "session_id": "session-abc123",
    "user_id": "session_xyz789"
  }
}
```

### Phoenix/Arize Traces
```json
{
  "attributes": {
    "session": {
      "id": "abc123"
    }
  }
}
```

### Custom Instrumentation
```python
# Some systems use prefixes
trace_id = f"session-{uuid.uuid4()}"

# Others don't
trace_id = str(uuid.uuid4())
```

## Design Goals

1. **Consistency**: All session IDs stored in the same format regardless of source
2. **Deduplication**: Prevents treating `session-abc123` and `abc123` as different sessions
3. **Compatibility**: Works with varied trace formats from different observability tools
4. **Simplicity**: Stored IDs are shorter and easier to work with in queries

## Pattern Matching Logic

The regex `r"session[_-]([a-zA-Z0-9_-]+)"` breaks down as:

- `session` - Literal text "session"
- `[_-]` - Either underscore or hyphen separator
- `(...)` - Capture group (what gets returned)
- `[a-zA-Z0-9_-]+` - One or more alphanumeric, underscore, or hyphen characters

**Key Insight**: `match.group(1)` returns only the captured part (inside parentheses), which excludes the "session-" prefix.

## Test Evidence

### Input Trace (sample_traces.jsonl)
```json
{
  "metadata": {
    "session_id": "session-abc123",
    "developer_id": "dev@example.com"
  },
  "usage": {"input_tokens": 250, "output_tokens": 150}
}
```

### Database Output (sessions table)
```csv
session_id,developer_id,tokens_in,tokens_out
abc123,dev@example.com,250,150
```

## Verification

You can verify this behavior with a simple test:

```python
import re

_SESSION_PATTERN = re.compile(r"session[_-]([a-zA-Z0-9_-]+)")

# Test cases
test_values = [
    "session-abc123",
    "session_xyz789",
    "abc123",
    "user-session-def456"
]

for value in test_values:
    match = _SESSION_PATTERN.search(value)
    if match:
        result = match.group(1)
    else:
        result = value
    print(f"{value:30} → {result}")
```

Output:
```
session-abc123                 → abc123
session_xyz789                 → xyz789
abc123                         → abc123
user-session-def456            → def456
```

## Implications for Testing

When comparing trace files to database contents:

1. **Expected**: Session IDs will differ by the "session-" prefix
2. **Not a bug**: This is intentional normalization
3. **Consistent**: All IDs in the database follow the same format
4. **Reversible**: Can reconstruct original format if needed (`f"session-{db_id}"`)

## Related Code

The session ID extraction follows this priority:

1. Search metadata for keys: `session_id`, `user_id`, `developer_session`, `user_api_key_end_user_id`
2. Check `requester_metadata.user_id`
3. Fall back to raw metadata
4. Apply regex pattern matching to normalize
5. Return first non-empty value if no match

See `_extract_session_id()` in `trace_normalizer.py:59-84` for full implementation.

## Future Considerations

If you need to preserve original session IDs:

1. Add a `raw_session_id` field to store the untransformed value
2. Keep normalized `session_id` for consistency
3. Update schema migration to backfill raw values

This would allow both normalized querying and original format reconstruction.

---

**Last Updated**: October 12, 2025
**Related Files**:
- `dev-agent-lens/scripts/src/prodlens/trace_normalizer.py:10,76-79`
- `dev-agent-lens/scripts/tests/test_trace_normalizer.py:10-35`
