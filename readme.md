
### Usage
- start a ftp server on your device
- on the client side run this script with server ip
- make sure "sync" folder is on both sides (server and client)

```text
usage: ftpsync [-h] [-p PORT] [-s SRC] [-d DIR] [-r] host

sync files from specific directory of FTP server

positional arguments:
  host             IP address of ftp server

options:
  -h, --help       show this help message and exit
  -p, --port PORT  PORT of ftp server (default: 2121)
  -s, --src SRC    REMOTE Directory which have to sync from
                   server (default: sync)
  -d, --dir DIR    LOCAL Directory (this device) (default:
                   sync)
  -r, --recursive  for syncing folder inside folder 
                   (default: False)
```

### Credits
[python docs](https://docs.python.org/3/library/index.html) for ftplib, datetime module in python
        
              

