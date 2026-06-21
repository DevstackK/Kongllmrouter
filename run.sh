#!/bin/bash
cd /mnt/c/Users/urfan/Desktop/Claude/kong-ai-gateway
venv/bin/python -c "
import traceback
try:
    import sys
    sys.path.insert(0, 'api')
    import index
    print('Import OK')
    index.app.run(host='0.0.0.0', port=5000)
except Exception as e:
    traceback.print_exc()
"
