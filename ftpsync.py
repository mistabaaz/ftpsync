from ftplib import FTP
from datetime import datetime, timezone
import os
import argparse

class ftp_sync:

    def __init__(self, host, port, local_dir, remote_dir, user="", passwd=""):
            
        self.host = host
        self.port = port
        self.local_dir = local_dir
        self.remote_dir = remote_dir.strip("/")

        if not os.path.exists(self.local_dir):
            print(f"{self.local_dir} directory dosen't exists")
            exit()

        self.ftp = FTP()

        self.ftp.connect(self.host, self.port)
        self.ftp.login(user, passwd)
        print(self.ftp.getwelcome(), "\n")

        dlst = self.remote_dir.split("/")
        if len(dlst) > 1:
            path = "/".join(dlst[0:-1])
        else:
            path = "."

        if dlst[-1] not in self.ftp.nlst(path):
            print(f"{self.remote_dir} directory dosen't exists on remote device")
            raise SystemExit
    
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
    parser = argparse.ArgumentParser(prog="ftpsync", description="sync files from specific directory of FTP server", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("host", help="IP address of ftp server")
    parser.add_argument("-p", "--port", type=int, default=2121, help="PORT of ftp server")
    parser.add_argument("-s", "--src", default="sync", help="REMOTE Directory which have to sync from server")
    parser.add_argument("-d", "--dir", default="sync", help="LOCAL Directory (this device)")
    args = parser.parse_args()

    client = ftp_sync(args.host, args.port, args.src, args.dir)

    client.sync()
    client.close()

if __name__ == "__main__":
    main()
