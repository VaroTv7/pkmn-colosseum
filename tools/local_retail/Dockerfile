# Disposable worker image for local retail validation.
#
# It contains only an interpreter and Ninja. Original game files, compilers,
# binutils and decomp tools are bind-mounted read-only at run time, and every
# input-bearing container runs with networking disabled. Never COPY originals,
# credentials or build outputs into this image.
FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home builder \
    && mkdir -p /w /out \
    && chown builder:builder /w /out

USER builder
WORKDIR /w
