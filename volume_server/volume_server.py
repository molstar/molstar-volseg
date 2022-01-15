from .i_volume_server import IVolumeServer


class VolumeServer(IVolumeServer):
    def root(self):
        return {"message": "Hello World"}

    def say_hello(self, user: str):
        return {"message": f"Hello {user}"}
    