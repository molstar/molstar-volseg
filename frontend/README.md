Running the example
===================


- Install conda (follow `../README.md`) and create environment


- Build example database (follow `../readme_db_build.md`)
  - EMD-1832: From <https://www.ebi.ac.uk/emdb/EMD-1832?tab=volume>, download `.map.gz` (in Download) and `.hff` (in Download segmentation at the bottom), extract to `preprocessor/data/raw_input_files/emdb/emd-1832/`
  - EMD-99999: From <https://drive.google.com/file/d/1mASvAFEvknjCQkeZd1xcz1YZV8iNXnYY/view?usp=sharing>, download `emd-99999.zip`, and extract it to to `preprocessor/data/raw_input_files/emdb/emd-99999/`
  - EMPIAR-10070: Download `archive.zip` (1.5GB) from <https://www.ebi.ac.uk/empiar/EMPIAR-10070/> and `.hff` from <https://www.ebi.ac.uk/empiar/volume-browser/empiar_10070_b3talongmusc20130301>, extract to `preprocessor/data/raw_input_files/empiar/empiar-10070/`

  ```sh
  # in the root dir of the cellstar-volume-server
  conda activate cellstar-volume-server
  python -m preprocessor.main --db_path db
  # entries should be created in db/emdb/, db/empiar
  ```

- Run the FastAPI server

  ```sh
  # in the root dir of the cellstar-volume-server
  conda activate cellstar-volume-server
  python main.py 
  # serves on localhost:9000
  ```


- Install and run frontend

  ```sh
  cd frontend/
  yarn
  yarn start
  # serves on localhost:3000
  ```

- It should be relatively easy to modify `frontend/src/model.ts` and `App.tsx` to show different entries/slices.

