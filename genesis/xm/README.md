# xm

## Overview

xm is a simple command line tool I use to do various actions when developing XiVO
on a remote server.

This tool is 100% XiVO specific.


## Usage

xm is made of a single make file allowing some operations on specific repositories.

I currently use an alias to make the invocation shorter

```
alias xm='make -f ~/dev/xm/Makefile XIVO_HOSTNAME=xivo-dev XIVO_PATH=~/dev/xivo'
```


### Syncing the local copy of xivo-ctid to a remote XiVO

```
make -f <path/to/xm>/Makefile cti.sync XIVO_PATH=<path/to/xivo/source/code> XIVO_HOSTNAME=<hostname>
```


## Sharing a dev folder with a XiVO

Some assumptions:

- The dev's machine host is 10.37.0.1
- We want to share with 10.37.0.0/16
- The dev's local dev folder is /home/pcm/dev/xivo
- The xivo's dev folder is /root/xivo

1. Install the NFS server on the host (Ubuntu)

```
sudo apt-get install nfs-server
```

2. Add the exported directories to */etc/exports*

```
/home/pcm/dev/xivo 10.37.0.0/16(rw,sync,no_root_squash,no_subtree_check)
```

3. Enable the exports

```
sudo exportfs -a
```

4. Install the NFS client on the XiVO

```
apt-get install nfs-client portmap
```

5. Test if the mount works, from the XiVO

```
mount 10.37.0.1:/home/pcm/dev/xivo /root/xivo
```

6. Add a line to */etc/fstab*

```
10.37.0.1:/home/pcm/dev/xivo /root/xivo nfs rw,hard,intr 0 0
```
