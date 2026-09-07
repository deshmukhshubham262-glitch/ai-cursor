from flask import Flask

app = Flask(__name__)


@app.get("/")
def home():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Virtual Mouse</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 3rem auto; max-width: 40rem; padding: 0 1.25rem; line-height: 1.6; }
    h1 { margin-bottom: 0.5rem; }
    .note { background: #f1f5f9; border-left: 4px solid #2563eb; padding: 1rem; }
  </style>
</head>
<body>
  <h1>AI Virtual Mouse</h1>
  <p class="note">The service is running successfully on Render.</p>
  <p>Web hosting cannot access your computer's webcam, display, or desktop pointer.</p>
  <p>Run <code>py -3.12 virtual_mouse.py</code> locally to use hand gestures.</p>
</body>
</html>"""
