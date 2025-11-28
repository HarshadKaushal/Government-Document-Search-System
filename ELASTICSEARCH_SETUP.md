# Elasticsearch Setup Guide

## Found Installation
Elasticsearch is installed at: `C:\elasticsearch\elasticsearch-8.17.4`

## Start Elasticsearch

### Option 1: Start in a new terminal window (Recommended)
1. Open a **new** Command Prompt or PowerShell window
2. Navigate to the Elasticsearch bin directory:
   ```powershell
   cd C:\elasticsearch\elasticsearch-8.17.4\bin
   ```
3. Run Elasticsearch:
   ```powershell
   .\elasticsearch.bat
   ```
4. Wait for it to fully start (you'll see "started" messages)
5. Keep this window open (don't close it - Elasticsearch runs in foreground)

### Option 2: Start as background service (if configured)
If Elasticsearch was installed as a Windows service:
```powershell
net start Elasticsearch
```

## Verify It's Running

After starting Elasticsearch, wait 10-15 seconds, then run:
```powershell
python check_elasticsearch.py
```

Or test in your browser: http://localhost:9200

You should see JSON output with Elasticsearch information.

## Important Notes

- **Default port**: 9200
- **Security**: By default, Elasticsearch 8.x may have security enabled
- If you see SSL/authentication errors, you may need to disable security or provide credentials

## Next Steps

Once Elasticsearch is running, proceed with indexing:
```powershell
python src/process_and_index.py
```

If Elasticsearch requires authentication, use:
```powershell
python src/process_and_index.py --es-password YOUR_PASSWORD
```

