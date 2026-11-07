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
        print(self.ftp.getwelcome(), "\n")
    
    def pull(self, file, bSize):
        print(f"Downloading file {file} ({bSize} B)")
        f = open(f"{self.local_dir}/{file}", "wb")
        res = self.ftp.retrbinary(f"RETR {file}", f.write, bSize) 
        print(res, "\n")
        f.close()

    def push(self, file, bSize):
        print(f"Uploading file {file} ({bSize} B)")
        f = open(f"{self.local_dir}/{file}", "rb")
        res = self.ftp.storbinary(f"STOR {file}", f, bSize)
        print(res)
        f.close()

    def MFMT_local(self, file, mtime):
        # change modify time of local files
        now = datetime.now(tz=timezone.utc).timestamp()
        os.utime(f"{self.local_dir}/{file}", times=(now, mtime))

    def sync(self):
        self.ftp.cwd(f"{self.remote_dir}")
    
        for file,facts in self.ftp.mlsd(facts=["size", "modify"]):
            
            rfsize = int(facts["size"])
            rdt = self.rfile_datetime(file, facts)

            # pull newly created remote files
            if not os.path.isfile(f"{self.local_dir}/{file}"):
                self.pull(file, rfsize)
                self.MFMT_local(file, rdt[1]) # modify time
                continue


            lfsize = os.stat(f"{self.local_dir}/{file}").st_size
            ldt = self.lfile_datetime(file)

            # check if remote file is new
            if (rdt[1]  > ldt[1]):
                self.pull(file, rfsize)
                self.MFMT_local(file, rdt[1]) # modify time

            elif (rdt[1] < ldt[1]):
                self.push(file, lfsize)
                res = self.ftp.sendcmd(f"MFMT {ldt[0]} {file}")
                print(res, "\n")
        
        # push newly created local files
        for file in os.listdir(self.local_dir):

            lfsize = os.stat(f"{self.local_dir}/{file}").st_size
            ldt = self.lfile_datetime(file)

            if file not in self.ftp.nlst():
                self.push(file, lfsize)
                res = self.ftp.sendcmd(f"MFMT {ldt[0]} {file}")
                print(res, "\n")

   
    def rfile_datetime(self, file, facts):
        # remote file modify time
        remote_mdate = facts["modify"].split(".")[0]
        remote_mtime = datetime.strptime(remote_mdate, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()

        return (remote_mdate, remote_mtime)

    def lfile_datetime(self, file):
        # local file modify time
        local_finfo = os.stat(f"{self.local_dir}/{file}")
        local_mtime_ = local_finfo.st_mtime
        local_mdate = datetime.fromtimestamp(local_mtime_, timezone.utc).strftime("%Y%m%d%H%M%S")
        local_mtime = datetime.strptime(local_mdate, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()

        return (local_mdate, local_mtime)

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
