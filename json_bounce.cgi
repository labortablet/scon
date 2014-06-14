#!/usr/bin/env python3

import sys
import json
import cgitb
cgitb.enable()

try:
	myjson = json.loads(sys.stdin.buffer.read().decode('utf-8'))
except Exception:
	print("Content-Type: text/html\n\n")
	print("<html><body><p>No valid JSON found</p></body></html>")
	sys.exit()

sys.stdout.buffer.write('Content-Type: application/json\n\n'.encode('utf-8'))
sys.stdout.buffer.write(json.dumps(myjson).encode('utf-8'))
