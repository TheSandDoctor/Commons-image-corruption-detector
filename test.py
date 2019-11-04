import mmap
name = "Cat"
with open('test.txt','rb',0) as file, \
                mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
	if s.find(b"" + bytes(name,'utf-8') + b"\n") != -1:
		print("T")
