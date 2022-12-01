import uvicorn

from app.settings import settings

if __name__ == "__main__":
    print("Cell* Volume Server")
    print(settings.dict())

    uvicorn.run(app="main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEV_MODE,
        ssl_keyfile=settings.CERT,
        ssl_certfile=settings.KEY,
        ssl_keyfile_password=settings.PASS
        )
