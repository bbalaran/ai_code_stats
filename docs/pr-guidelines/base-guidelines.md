# Base Code Review Guidelines

**Purpose**: Canonical protocols and reusable patterns for all PRs

## 🎯 Core Development Principles

### Evidence-Based Development
- **Verify Before Modify**: Reproduce bugs and understand root causes before suggesting fixes
- **Test-Driven Resolution**: Write tests for bug scenarios before implementing fixes
- **Incremental Changes**: Small, atomic modifications that can be tested independently
- **Defensive Validation**: Input checks for untrusted sources, skip excessive validation for trusted APIs

### Solo Developer Security Focus
- **Practical Security**: Focus on real vulnerabilities (command injection, credential exposure, path traversal)
- **Context-Aware Analysis**: Distinguish trusted sources (GitHub API, npm registry) from untrusted user input
- **Filter Enterprise Paranoia**: Skip theoretical concerns and JSON schema validation for trusted APIs
- **Fail Fast, Fail Loud**: No silent fallbacks - errors should be explicit and actionable

### Quality Standards
- **Zero Regressions**: Changes must not introduce new bugs
- **High Code Coverage**: 80-90% test coverage for critical paths
- **Maintainable Codebase**: Fixes should improve readability and modularity
- **CI Parity**: All code must run deterministically in CI vs local environments

## 🚫 Anti-Patterns to Avoid

### ❌ **Subprocess Without Timeouts**
**Problem**: Subprocesses without timeouts can hang indefinitely
```python
# Wrong
subprocess.run(["command"])
```
**Solution**: Always use timeouts
```python
# Correct
subprocess.run(["command"], timeout=30)
```

### ❌ **Silent Fallbacks on Errors**
**Problem**: Masking errors makes debugging impossible
```python
# Wrong
try:
    risky_operation()
except:
    pass  # Silent failure
```
**Solution**: Explicit error handling
```python
# Correct
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

### ❌ **Skipping Tests in CI**
**Problem**: Skip decorators bypass critical validation
```python
# Wrong
@pytest.mark.skip("Flaky test")
def test_critical_feature():
    ...
```
**Solution**: Fix the test or remove it
```python
# Correct - Fix root cause
def test_critical_feature():
    # Properly isolated test with deterministic setup
    ...
```

### ❌ **Untrusted Input Without Sanitization**
**Problem**: User input directly used in commands or queries
```python
# Wrong
os.system(f"process {user_input}")
```
**Solution**: Sanitize and validate
```python
# Correct
import shlex
safe_input = shlex.quote(user_input)
subprocess.run(["process", safe_input], timeout=30)
```

### ❌ **Enterprise Paranoia for Trusted Sources**
**Problem**: Excessive validation for verified APIs
```python
# Wrong - GitHub API responses don't need schema validation
response = requests.get("https://api.github.com/repos/...")
validate_complex_schema(response.json())  # Unnecessary
```
**Solution**: Trust verified sources
```python
# Correct
response = requests.get("https://api.github.com/repos/...")
response.raise_for_status()  # HTTP errors only
data = response.json()  # Trust GitHub API structure
```

## 📋 Tool Selection Hierarchy

### Serena MCP (Preferred for Code Operations)
- **Symbol-level operations**: `find_symbol`, `replace_symbol_body`
- **File operations**: `read_file`, `create_text_file`
- **Search operations**: `search_for_pattern`, `find_referencing_symbols`
- **Advantages**: Semantic understanding, precise edits, context-aware

### Read Tool (Fallback for Simple Reads)
- When Serena MCP unavailable or simple file reading needed
- Direct file access without symbol analysis

### Bash Commands (Last Resort)
- Only when Serena MCP and Read tool insufficient
- Use for git operations, system commands, test execution
- Never use for file content manipulation (cat, sed, awk)

## 🔧 Testing & CI Safety

### Subprocess Discipline
- **Always** use `timeout` parameter in subprocess calls
- **Never** use `shell=True` with user input
- **Always** validate command arguments

### Skip Pattern Elimination
- **Zero tolerance** for `@pytest.mark.skip` in CI
- Fix flaky tests or remove them entirely
- Use `@pytest.mark.skipif` only for environment-specific conditions

### CI Parity Validation
- Tests must pass identically in local and CI environments
- No environment-specific hacks or workarounds
- Deterministic test data and setup

## 🎯 Quality Gates

### Before Merge Checklist
- [ ] All tests pass (no skips)
- [ ] Code coverage maintained or improved
- [ ] No regression in existing functionality
- [ ] Security vulnerabilities addressed (real threats only)
- [ ] CI parity validated
- [ ] Documentation updated if needed

### Security Review Focus
- Command injection vulnerabilities
- Credential exposure in code or logs
- Path traversal attacks
- SQL injection (dynamic queries)
- XSS vulnerabilities (web applications)
- Authentication/authorization flaws

---

**Last Updated**: 2025-10-12
**Version**: 1.0
