# Data Analyst Agent API

## POST /api/

Accepts:
- questions.txt (required)
- Additional files (CSV, JSON, PNG, etc.)

Returns:
- JSON array or object in exact requested format
- Base64-encoded plot if requested

### Example
curl -X POST "https://<your-url>/api/" \
  -F "files=@questions.txt" \
  -F "files=@data.csv"
