# TODO: is there a better way to do this other than having to pip install -e . for the imports to work?
import setuptools
setuptools.setup(
  name='cellstar-volume-server',
  version='0.1',
  packages=setuptools.find_packages(
    include=["db/", "preprocessor/", "volume_server/"]
  )
 )