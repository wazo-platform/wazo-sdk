# wazo-sdk

Developer tool kit for Wazo development


## Installation

`wdk` depends on lsyncd. It can be installed on a Debian or Ubuntu with the following
commands

```sh
sudo apt update
sudo apt install lsyncd
```

The recommended way to install `wdk` is to use a virtual environment.

```sh
mkvirtualenv --python /usr/bin/python3 wdk
pip install -r requirements.txt
pip install .
sudo ln -s ~/.virtualenvs/wdk/bin/wdk /usr/local/bin/wdk
```

Copying configuration files. The following commands will create a copy of the sample
configuration file that you can modify to fit your needs and will create a link to the
version controlled `project.yml` such that changes to file will be automatically applied
when pulling.

```sh
mkdir -p ~/.config/wdk
cp config.yml.sample ~/.config/wdk/config.yml
ln -s $(readlink -f project.yml) ~/.config/wdk/project.yml
```


## Configuration

The default location of the configuration file is `~/.config/wdk/config.yml` you can check
`config.yml.sample` for an example.

If you wish to use another location for you configuration file you can use the `--config` flag
when launching `wdk` or set the `WDK_CONFIG_FILE` environment variable to the config file location.


### Project configuration

Until everything can be guessed from the projects source code some information have to be configured
for each project. This information is stored in the project file. The default project file location
is `~/.config/wdk/project.yml`.

The project file has the following structure

```yml
<project name>:
  python2: true
  python3: true
  binds:
    <source>: <destination>
  clean:
    - </file/to/remove/when/done>
```

* project name: This is the name that matches your local source directory. ex: `wazo-auth`
* python2: If this project is a python2 project. This will do a `python2 setup.py develop`
* python3: Same as python2 but for python3 project. This will do a `python3 setup.py develop`
* binds: This is a map of source and destination file/directory that should be overridden.
* clean: A list of files to delete when unmounting the project.

Note that using bind on files will not follow changes to the file. If you use a bind on a
configuration file for example the mount will have to be redone when you change the configuration
file.

Note that new entry points will need the project to be unmounted and mounted again to be applied.


## Mounting a project

```sh
wdk mount [<project1>, <project2>, ...<projectn>]
```

## Unmounting a project

```sh
wdk umount [<project1>, <project2>, ...<projectn>]
```

## Listing mounted projects

```sh
wdk mount --list
```
