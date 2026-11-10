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

        self.total_size = 0
        self.start_time = datetime.now(tz=timezone.utc).timestamp()

        self.ftp = FTP()

        if not os.path.exists(self.local_dir):
            print(f"{self.local_dir} directory dosen't exists locally")
            raise SystemExit 

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
        self.total_size += bSize
        print(f"Downloading file {file} {(bSize/1048576):.2f} MB ({bSize} B)")
        f = open(f"./{file}", "wb")
        res = self.ftp.retrbinary(f"RETR {file}", f.write, bSize) 
        print(res, "\n")
        f.close()

    def push(self, file, bSize):
        self.total_size += bSize
        print(f"Uploading file {file} %.2f {(bSize/1048576):.2f} MB ({bSize} B)")
        f = open(f"./{file}", "rb")
        res = self.ftp.storbinary(f"STOR {file}", f, bSize)
        print(res)
        f.close()

    def MFMT_local(self, file, mtime):
        # change modify time of local files
        now = datetime.now(tz=timezone.utc).timestamp()
        os.utime(f"./{file}", times=(now, mtime))

    def sync(self, rdir, ldir, recursive):
        # changing lcoal & remote current directory
        self.ftp.cwd(f"{rdir}")
        os.chdir(ldir)
    
        for file,facts in self.ftp.mlsd(facts=["type", "size", "modify"]):
            
            if (facts["type"]=="dir" and recursive):
                print(f"\nfetching subdirectory '{self.ftp.pwd()}/{file}'\n")
                if not os.path.exists(file):
                    os.mkdir(file)
                self.sync(file, file, recursive);
                continue
            elif (facts["type"]=="dir"):
                print(f"skipped directory '{file}' (use -r for sync)\n")
                continue

            rfsize = int(facts["size"])
            rdt = self.rfile_datetime(file, facts)

            # pull newly created remote files
            if not os.path.isfile(f"./{file}"):
                self.pull(file, rfsize)
                self.MFMT_local(file, rdt[1]) # modify time
                continue


            lfsize = os.stat(f"./{file}").st_size
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
        for file in os.listdir():

            if ( os.path.isdir(file) and recursive ):
                if file not in self.ftp.nlst():
                    print(f"\nsyncing subdirectory '{os.getcwd()}/{file}'\n")
                    self.ftp.mkd(file)
                    self.sync(file, file, recursive);
                continue
            elif ( os.path.isdir(file) ):
                if file not in self.ftp.nlst():
                    print(f"skipped directory '{file}' (use -r for sync)\n")
                continue

            lfsize = os.stat(f"./{file}").st_size
            ldt = self.lfile_datetime(file)

            if file not in self.ftp.nlst():
                self.push(file, lfsize)
                res = self.ftp.sendcmd(f"MFMT {ldt[0]} {file}")
                print(res, "\n")

        # directory complete go back
        print(f"Directory '{rdir}' synced successfully\n")
        self.ftp.cwd("./..")
        os.chdir("./..")
   
    def rfile_datetime(self, file, facts):
        # remote file modify time
        remote_mdate = facts["modify"].split(".")[0]
        remote_mtime = datetime.strptime(remote_mdate, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()

        return (remote_mdate, remote_mtime)

    def lfile_datetime(self, file):
        # local file modify time
        local_finfo = os.stat(f"./{file}")
        local_mtime_ = local_finfo.st_mtime
        local_mdate = datetime.fromtimestamp(local_mtime_, timezone.utc).strftime("%Y%m%d%H%M%S")
        local_mtime = datetime.strptime(local_mdate, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()

        return (local_mdate, local_mtime)

    def close(self):
        self.ftp.close()

    def __del__(self):
        self.ftp.close()

        total_sec = datetime.now(tz=timezone.utc).timestamp() - self.start_time
        speed = (self.total_size / 1048576) / total_sec
        print (f"\nTook {total_sec//60:.0f}m {total_sec%60:.0f}s!", "Average Speed : %.2f MB/sec" % speed)

def main():
    parser = argparse.ArgumentParser(prog="ftpsync", description="sync files from specific directory of FTP server", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("host", help="IP address of ftp server")
    parser.add_argument("-p", "--port", type=int, default=2121, help="PORT of ftp server")
    parser.add_argument("-s", "--src", default="sync", help="REMOTE Directory which have to sync from server")
    parser.add_argument("-d", "--dir", default="sync", help="LOCAL Directory (this device)")
    parser.add_argument("-r", "--recursive",action="store_true", help="for syncing folder inside folder")
    args = parser.parse_args()

    client = ftp_sync(args.host, args.port, args.src, args.dir)

    client.sync(args.dir, args.src, args.recursive)
    client.close()

if __name__ == "__main__":
    main()
