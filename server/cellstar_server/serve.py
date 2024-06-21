import argparse
from pathlib import Path
import uvicorn
from cellstar_server.app.settings import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    args = parser.parse_args()
    
    print("Mol* Volume Server")
    print(settings.dict())
    if args.ssl_certfile and args.ssl_keyfile:
        uvicorn.run(
               app="main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEV_MODE,
               ssl_keyfile=str(Path(args.ssl_keyfile).resolve()),
               ssl_certfile=str(Path(args.ssl_certfile).resolve())
               )
    if not args.ssl_certfile and not args.ssl_keyfile:
        uvicorn.run(
            app="main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEV_MODE
        )
    else:
        print("ssl_certfile or ssl_keyfile was not provided")
