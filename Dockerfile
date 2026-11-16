FROM gcr.io/distroless/python3-debian13:nonroot

ARG VERSION=v0.0.1

ENV APP_VERSION=${VERSION} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src"

LABEL org.opencontainers.image.version="${VERSION}"

WORKDIR /app

COPY --chown=65532:65532 . .

USER 65532:65532

CMD ["-m", "logdigest"]
