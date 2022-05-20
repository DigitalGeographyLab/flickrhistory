# Download a complete history of georeferenced flickr posts

This is a Python script that can download a complete history of georeferenced flickr photo metadata. It uses the official flickr API, and saves the data into a PostgreSQL/PostGIS database.

The script will download all photos until its starting time, and keep track of already downloaded time periods in a cache file (default location `~/.cache/flickrhistory.yml`). Upon restart it will catch up until the new starting time.

*Flickrhistory* makes use of multiple threads and can use multiple API keys (something that most likely disagrees with flickr’s T&C, use feature at your own risk).

If you use *flickrhistory* for scientific research, please cite it in your publication: <br />
> Fink, C. (2020): *flickrhistory: a Python tool to download a complete flickr timeline*. [doi:10.5281/zenodo.6566196](https://doi.org/10.5281/zenodo.6566196).

<!--//
TODO: create separate repository containing a one-stop-shop script for updating the HELICS/DGL dataset, and add a link for Vuokko, Wäeski and co here.
//-->

![screen shot](extra/images/screenshot.png)

### Dependencies

The script is written in Python 3 and depends on the Python modules [blessed](https://blessed.readthedocs.io/), [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/), [psycopg2](https://www.psycopg.org/), [PyYaml](https://pyyaml.org/), [Requests](https://2.python-requests.org/en/master/) and [SQLAlchemy](https://sqlalchemy.org/).

### Installation

- Download the latest [release](https://gitlab.com/christoph.fink/flickrhistory/-/releases), and use `pip` to install *flickrhistory* and its dependencies:

```shell
pip3 install flickrhistory-0.0.0.tar.gz
```

### Configuration

Copy the example configuration file [flickrhistory.yml.example](https://gitlab.com/christoph.fink/flickrhistory/-/raw/master/flickrhistory.yml.example) to a suitable location, depending on your operating system: 

- on Linux systems:
    - system-wide configuration: `/etc/flickrhistory.yml`
    - per-user configuration: 
        - `~/.config/flickrhistory.yml` OR
        - `${XDG_CONFIG_HOME}/flickrhistory.yml`
- on MacOS systems:
    - per-user configuration:
        - `${XDG_CONFIG_HOME}/flickrhistory.yml`
- on Microsoft Windows systems:
    - per-user configuration:
        `%APPDATA%\flickrhistory.yml`

Adapt the configuration:

- Configure a PostgreSQL connection string (`connection_string`), pointing to an existing database (with the PostGIS extension enabled).
- Configure one or more API [access keys](https://flickr.com/services/api/keys/) to the flickr API `flickr_api_keys`). Using more than one API key in all likelihood violates the Terms and Conditions of the Flickr API (don’t do it!).

If you have a cache file from a previous installation in which already downloaded time periods are saved, copy it to `${XDG_CACHE_HOME}/flickrhistory.yml` or `%LOCALAPPDATA%/flickrhistory.yml` on Linux or MacOS, and Microsoft Windows, respectively.

### Usage

#### Command line executable

```shell
python -m flickrhistory
```

#### Python

Import the `flickrhistory` module. Instantiate a `FlickrHistoryDownloader`, and call its `download()` method.

```python
import flickrhistory

downloader = flickrhistory.FlickrHistoryDownloader()
downloader.download()
```
