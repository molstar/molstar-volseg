import uvicorn

from volume_server.settings import settings

if __name__ == '__main__':
    print("Cell* Volume Server")
    print(settings.dict())
    uvicorn.run(
        app="volume_server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEV_MODE
    )
    
