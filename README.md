# wazo-sdk

Developer tool kit for Wazo development


## Installation

`wdk` depends on lsyncd. It can be installed on a Debian or Ubuntu with the following
commands. If you running on macOS, lsyncd won't work, so you must set `rsync_only` option to `true`.

### Installing WDK
The recommended way to install `wdk` is to use a virtual environment.

#### Debian Instructions
```sh
sudo apt update
sudo apt install lsyncd virtualenvwrapper python3-dev
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
mkvirtualenv --python /usr/bin/python3 wdk
```

#### macOS Instructions
```sh
brew install rsync # install latest
brew install python # install python3
# Reload your terminal session to have the latest rsync
pip install --user virtualenvwrapper
mkdir -p ~/.virtualenvs
virtualenv -p python3 ~/.virtualenvs/wdk
source ~/.virtualenvs/wdk/bin/activate
```

#### WDK Dependencies
```sh
pip install -r requirements.txt
pip install -e .
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

### On the target machine (Wazo)

```sh
apt update
apt install rsync
mkdir /usr/src/wazo  # or whatever your <local_source>
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
  log_filename: <path-to-filename.log>  # default to /var/log/<project name>.log
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
wdk mount [-r] [<project1>, <project2>, ...<projectn>]
```

## Unmounting a project

```sh
wdk umount [-r] [<project1>, <project2>, ...<projectn>]
```

## Listing mounted projects

```sh
wdk mount --list
```

## Restarting a daemon

```sh
wdk restart [<project1>, <project2>]
```

## Cloning all repos from GitHub

```sh
wdk repo clone
```
`wdk` will ask for your login/password and clone every repo of the GitHub orgs listed in the config.

## Tailing a log files

```sh
wdk tailf <project>
```

## Troubleshooting

### Common causes

Make sure:

* you have created your `<remote_source>` (`/usr/src/wazo` by default)
* you have installed rsync on your target marchine

### Increase verbosity of errors

```sh
wdk -vvv <command>
```

### Mount command is stuck

Copy the lsyncd command (got from `wdk -vvv ...`) and run it with the `-nodaemon` argument, e.g.:

```sh
lsyncd -nodaemon -delay 1 -rsyncssh /home/user/git/origin/wazo-confd wazo.example.com /usr/src/wazo/wazo-confd
```

### Increasing the amount of inotify watchers

* `echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p`

For more information: https://github.com/guard/listen/wiki/Increasing-the-amount-of-inotify-watchers

## The state file

The state file contains information about the current state of wdk.

The file is located in `~/.local/cache/wdk/state`

```json
{
    "hosts": {
        "<hostname>": {
            "mounts": {
                <project_name>: {
                    "project": "<project name>",
                    "lsync_config": "</path/to/the/lsync/config/file>",
                }
            }
        }
    }
}
```
