from ftplib import FTP
import os
from datetime import datetime, timezone

class ftp_sync:

    host = "127.0.0.1"
    port = 2121
    local_dir = "sync"
    remote_dir = "sync"

    ftp = FTP()

    def init(self):
        self.ftp.connect(self.host, self.port)
        self.ftp.login('', '')
        print(self.ftp.getwelcome())
    
    def pull(self, file, bSize):
        print(f"pull file {file} {bSize}B")
        f = open(f"{self.local_dir}/{file}", "wb")
        self.ftp.retrbinary(f"RETR {file}", f.write, bSize) 
        f.close()

    def push(self, file, bSize):
        print(f"push file {file} {bSize}B")
        f = open(f"{self.local_dir}/{file}", "rb")
        self.ftp.storbinary(f"STOR {file}", f, bSize)
        f.close()

    def sync(self):
        self.ftp.cwd(f"{self.remote_dir}")
    
        # pull remote files or push newer
        for file,facts in self.ftp.mlsd(facts=["size", "modify"]):
            # remote file size and modify time
            remote_fsize = int(facts["size"])
            remote_mdate = float(facts["modify"])

            # local modify time and size
            if not os.path.isfile(f"{self.local_dir}/{file}"):
                self.pull(file, remote_fsize)
                continue

            local_finfo = os.stat(f"{self.local_dir}/{file}")
            local_mtime = local_finfo.st_mtime
            local_mdate = float(datetime.fromtimestamp(local_mtime, timezone.utc).strftime("%Y%m%d%H%M%S.%f"))
            local_fsize = local_finfo.st_size
           
            if (remote_mdate > local_mdate):
                self.pull(file, remote_fsize)
            else:
                self.push(file, local_fsize)
        
        # push newly created local files
        for file in os.listdir(self.local_dir):
            local_finfo = os.stat(f"{self.local_dir}/{file}")
            local_fsize = local_finfo.st_size
            if file not in self.ftp.nlst():
                self.push(file, local_fsize)
   
    def close(self):
        self.ftp.close()

    def __del__(self):
        self.ftp.close()

def main():
    client = ftp_sync()
    client.remote_dir = "redmi9i/sync_t"

    client.init()
    client.sync()
    client.close()

if __name__ == "__main__":
    main()
