from flask import Flask
app = Flask(__name__)
@app.route('/health')
def health_check():
    return {'status': 'ok', 'service': 'deep-packet-dashboard'}

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response

if __name__ == '__main__':
    app.run(port=5000)
