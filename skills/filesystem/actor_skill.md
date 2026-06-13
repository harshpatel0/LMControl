# Filesystem — Actor Guide

Provides file operations on the local filesystem.

## Actions

### create_file
Creates a new file. Optionally writes initial content.
```json
{"action": "create_file", "path": "C:\\path\\to\\file.txt", "content": "optional content"}
```
- `path` (required) — Absolute path to the file.
- `content` (optional) — Text to write on creation. If omitted, file is created empty.

### write_to_file
Overwrites a file with new content.
```json
{"action": "write_to_file", "path": "C:\\path\\to\\file.txt", "content": "new content"}
```
- `path` (required) — Absolute path to the file.
- `content` (required) — Text to write (replaces existing content).

### read_file
Reads and returns the full contents of a file.
```json
{"action": "read_file", "path": "C:\\path\\to\\file.txt"}
```
- `path` (required) — Absolute path to the file.

### append_file
Appends content to the end of an existing file.
```json
{"action": "append_file", "path": "C:\\path\\to\\file.txt", "content": "text to append"}
```
- `path` (required) — Absolute path to the file.
- `content` (required) — Text to append.

### present_file
Opens the file with the system default application (like double-clicking in Explorer).
```json
{"action": "present_file", "path": "C:\\path\\to\\file.txt"}
```
- `path` (required) — Absolute path to the file.

### delete_file
Deletes a file. A confirmation dialog will pop up — the user must click **Yes** to proceed.
```json
{"action": "delete_file", "path": "C:\\path\\to\\file.txt"}
```
- `path` (required) — Absolute path to the file.
- **Warning:** A Windows dialog prompts the user for permission. If denied, the action fails.

## Notes
- Use **absolute paths only**. Relative paths are not supported.
- All actions use UTF-8 encoding.
- If a file does not exist, `read_file` and `append_file` will fail.
