#!/usr/local/bin/python3.12
def application(environ, start_response):
    import sys
    import site
    
    status = '200 OK'
    output = b'Python Path:\n'
    
    # Show sys.path
    for p in sys.path:
        output += f"{p}\n".encode('utf-8')
    
    output += b"\nInstalled Packages:\n"
    
    # Try to import packages
    try:
        import flask
        output += b"Flask is installed\n"
    except ImportError:
        output += b"Flask is NOT installed\n"
    
    try:
        import numpy
        output += b"NumPy is installed\n"
    except ImportError:
        output += b"NumPy is NOT installed\n"
    
    response_headers = [('Content-type', 'text/plain'),
                      ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    
    return [output]