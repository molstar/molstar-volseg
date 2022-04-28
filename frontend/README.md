Running the example
===================

- Install ciftools

```
# activate venv
git clone https://github.com/molstar/ciftools-python.git
cd ciftools-python
pip install msgpack-python # TODO: add requirements file to the ciftools repo
pip install -e . 
```

- Run the FastAPI server

```
# in the root dir of the cellstar-volume-server
pip install uvicorn  # if not installed
uvicorn main:app --port 9000 --reload
```

- Install and run frontend

```
cd frontend
yarn
yarn start
```

- The example expects emd-1832 and emd-99999 (the example from BioImage Archive) to be in the "db"

- This should open ``localhost:3000`` with the example and everything should work.

- It should be relatively easy to modify ``frontend/src/model.ts`` and ``App.tsx`` to show different entries/slices.

