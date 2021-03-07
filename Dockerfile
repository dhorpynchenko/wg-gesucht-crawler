FROM python:3.6-alpine

WORKDIR /app/
COPY ./ /app/

RUN apk add --no-cache --virtual .build-deps gcc libc-dev libxslt-dev && \
    apk add --no-cache libxslt && \
    pip install -r requirements.txt && \
    apk del .build-deps

CMD ["python","-u","main.py"]