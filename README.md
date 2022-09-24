# cellstar-volume-server
Cell* Volume Server


zarr package (a requirement for this project) requires C++ dev-kit in order to install (you can get with visual studio installer for example, mingw)


# run server 


```
cd volume_server
python main.py
```

or 

```
cd volume_server
uvicorn server:app --port 9000 --reload  # other params
```

## Settings

Environment variables (with defaults):

- `HOST=0.0.0.0` where to host the server
- `PORT=9000` what port to run the app on
- `DB_PATH=db` path to the root of the database
- `DEV_MODE=False` if True, runs the server in reload mode

Linux/Mac

```
cd volume_server
DEV_MODE=True python main.py
```

Windows

```
cd volume_server
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