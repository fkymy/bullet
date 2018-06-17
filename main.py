
# [START app]
import os
import sys
import logging
import tempfile
import errno

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, AudioMessage, TextSendMessage
)

app = Flask(__name__)

# ACCESS_TOKEN = 'EayIwmR9wSGAd2d+c49vjErYHI+myz06mwqhSqdm46RrEehI1NHJ6PvvSBJJdBFIxZtjexNCSVBVLl9Px/jznYaMcpv2ZWwV4BtHWC6mhbjeX+v0KlcfWcRV8fgkuszWcNOlp52rDpu2OsvvtO/ZewdB04t89/1O/w1cDnyilFU='
#
# CHANNEL_SECRET = '9862032ed68823de2b01b02b6e2ca998'
channel_access_token = os.environ.get("LINE_ACCESS_TOKEN", None)
channel_secret = os.environ.get("LINE_CHANNEL_SECRET", None)

if channel_secret is None:
    print('env_variable: LINE_CHANNEL_SECRET is not set')
    sys.exit(1)
if channel_access_token is None:
    print('env_variable: LINE_ACCESS_TOKEN is not set')

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secrete)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# create tmp dir for downloadable content
def make_static_temp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World!'

@app.route('/callback', methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
