FROM gcr.io/google-appengine/python
LABEL python_version=python3.6
RUN virtualenv --no-download /env -p python3.6

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD requirements.txt /app/

RUN apt-get update
RUN apt-get install libopus-dev -y
RUN apt-get install libsodium-dev -y
RUN apt-get update && apt-get install -y \
      wget \
      xz-utils
RUN wget http://johnvansickle.com/ffmpeg/releases/ffmpeg-release-64bit-static.tar.xz \
      && tar Jxvf ./ffmpeg-release-64bit-static.tar.xz \
      && cp ./ffmpeg*64bit-static/ffmpeg /usr/local/bin/

RUN pip install -r requirements.txt
ADD . /app/
CMD exec gunicorn -b :$PORT main:app
