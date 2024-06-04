import uvicorn
from cellstar_server.app.settings import settings

if __name__ == "__main__":
    print("Mol* Volume Server")
    print(settings.dict())

    uvicorn.run(
        app="main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEV_MODE
    )
