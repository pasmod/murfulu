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
"""

import asyncio


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
    server_r, server_w = await asyncio.open_connection("elasticsearch", 9200)
    try:
        await asyncio.gather(pipe(client_r, server_w), pipe(server_r, client_w))
    finally:
        server_w.close()
        client_w.close()


async def main() -> None:
    """Listen on every interface of the container; publish only on 127.0.0.1."""
    server = await asyncio.start_server(handle, "0.0.0.0", 9201)
    async with server:
        await server.serve_forever()


asyncio.run(main())
