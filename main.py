
# [START app]
import os
import io
import sys
import logging
import tempfile
import errno
import ffmpeg
from argparse import ArgumentParser

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    AudioMessage, AudioSendMessage
)

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


app = Flask(__name__)

# for gae
# channel_access_token = os.environ.get("LINE_ACCESS_TOKEN", None)
# channel_secret = os.environ.get("LINE_CHANNEL_SECRET", None)

channel_access_token = os.getenv("LINE_ACCESS_TOKEN", None)
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)

if channel_secret is None:
    print('env_variable: LINE_CHANNEL_SECRET is not set')
    sys.exit(1)
if channel_access_token is None:
    print('env_variable: LINE_ACCESS_TOKEN is not set')


line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
speech_client = speech.SpeechClient()


static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
test_audio_file = None

# create tmp dir for downloadable content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


def decode_audio(in_filename, **input_kwargs):
    try:
        out, err = (ffmpeg
            .input(in_filename, **input_kwargs)
            .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        logging.exception("ffmpeg error decoding audio:\n " + e)
        sys.exit(1)
    return out


def get_transcripts(audio_data):
    audio = types.RecognitionAudio(content=audio_data)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='ja-JP'
    )
    response = client.recognize(config, audio)
    return [result.alternatives[0].transcript for result in response.results]


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World!'


# [START handler]
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
    """testers
    """
    reply = None

    if event.message.text == 'ping':
        reply = TextSendMessage(text='ping')

    elif event.message.text == 'hm':
        # with io.open(os.path.join(temporary_path, 'moe.m4a'), 'rb') as af:
        #     content = af.read()
        reply = AudioSendMessage(original_content_url=os.path.join(os.path.dirname(__file__), 'moe.m4a'))

    line_bot_api.reply_message(
        event.reply_token,
        reply
    )


@handler.add(MessageEvent, message=AudioMessage)
def handle_content_message(event):
    """Return transcript
    """

    if isinstance(event.message, AudioMessage):
        extension = 'm4a'
    else:
        return

    # get_message_content makes http get request to Get Content API
    # https://devdocs.line.me/en/#get-content
    # Content.content is audio/x-m4a
    content = line_bot_api.get_message_content(event.message.id)

    app.logger.info('WRITING M4A RETURNED FROM LINE')
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=extension+'-', delete=False) as tf:
        for chunk in content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + extension
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    # nani kore~
    # app.logger.info('PREPROCESS AUDIO')
    # aac_audio = AudioSegment.from_file(os.path.join(static_tmp_path, dist_name))
    # can't you export AudioSegment obj?: processed = AudioSegment(data=content)
    # aac_audio.export(os.path.join(static_tmp_path, 'preprocessed.FLAC'), format='FLAC')

    # with io.open(os.path.join(static_tmp_path, 'preprocessed.FLAC'), 'rb') as af:
    #     content = af.read()
    #     audio = types.RecognitionAudio(content=content)

    # ? can we preprocess flac from content returned by get_message_content?
    # flac_content = AudioSegment.from_file(os.path.join(temporary_path, dist_name), format='FLAC')
    # app.logger.info(flac_content)
    # app.logger.info(type(flac_content))
    # audio = types.RecognitionAudio(content=content)

    reply = ''
    audio_data = decode_audio(os.path.join(static_tmp_path, dist_name))
    transcripts = get_transcripts(audio_data)
    for transcript in transcripts:
        reply = reply + transcript.encode('utf-8')

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(reply)
    )


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
# [END handler]


if __name__ == '__main__':
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8080, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    make_static_tmp_dir()

    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
