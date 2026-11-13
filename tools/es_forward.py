"""Forward port 9201 to the stack's Elasticsearch, for a corpus build on the Mac.

The stack's Elasticsearch publishes no port, and a build in a container is
capped by Docker Desktop's memory — 7.7 GB on the Mac, shared with everything
else Docker runs — while v15 peaked at 7.2 GB. So the build runs on the Mac
itself (tools/build_corpus_mac.sh) and reaches Elasticsearch through this, run
in a throwaway container of the api image and published on 127.0.0.1 only::

    docker run -d --rm --name murfulu-es-forward --network murfulu_default \
      -p 127.0.0.1:9201:9201 -v "$PWD/tools/es_forward.py:/fwd.py:ro" \
      --memory 128m murfulu-api:latest python /fwd.py
    # … build …
    docker stop murfulu-es-forward

**The same forwarder reaches the API and Postgres**, for the browser suite and
the live tests against the stack (docs/ENGINEERING.md, Tests): give it the
port to listen on, the service and its port — ``python /fwd.py 8010 api 8000``
or ``python /fwd.py 5433 db 5432`` — and publish that port on 127.0.0.1.
"""

import asyncio
import sys

#: Where to listen and what to join, from the command line or Elasticsearch's.
LISTEN, TARGET, TARGET_PORT = (
    (int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
    if len(sys.argv) == 4
    else (9201, "elasticsearch", 9200)
)


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Copy one direction until it ends, then pass the end on — a half-close.

    Closing the whole connection when one side stops sending would drop the
    answer still on its way back; ``write_eof`` ends only this direction.
    """
    while data := await reader.read(65536):
        writer.write(data)
        await writer.drain()
    if writer.can_write_eof():
        writer.write_eof()


async def handle(
    client_r: asyncio.StreamReader, client_w: asyncio.StreamWriter
) -> None:
    """Join one client to Elasticsearch, both ways, and close when both end."""
    server_r, server_w = await asyncio.open_connection(TARGET, TARGET_PORT)
    try:
        await asyncio.gather(pipe(client_r, server_w), pipe(server_r, client_w))
    finally:
        server_w.close()
        client_w.close()


async def main() -> None:
    """Listen on every interface of the container; publish only on 127.0.0.1."""
    server = await asyncio.start_server(handle, "0.0.0.0", LISTEN)
    async with server:
        await server.serve_forever()


asyncio.run(main())
