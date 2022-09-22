# cellstar-volume-server
Cell* Volume Server


zarr package (a requirement for this project) requires C++ dev-kit in order to install (you can get with visual studio installer for example, mingw)


# run server 


```
python main.py
```

or 

```
uvicorn volume_server.main:app --port 9000 --reload  # other params
```

## Settings

Environment variables (with defaults):

- `HOST=0.0.0.0` where to host the server
- `PORT=9000` what port to run the app on
- `DB_PATH=db` path to the root of the database
- `DEV_MODE=False` if True, runs the server in reload mode

Linux/Mac

```
DEV_MODE=True python main.py
```

Windows

```
set DEV_MODE=True && python main.py
```

# Conda/Mamba

```
conda env create -f environment.yaml  # or update
conda activate cellstar-volume-server
```

Mamba is a lot faster for creating/updating envs:

```
mamba env create -f environment.yaml  # or update
```