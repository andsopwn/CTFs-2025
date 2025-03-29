# Container
The server may be slow, so you don't have to be in a hurry. 
`pow.py` is a script for configuring a challenge environment; you don't need to analyze it.
The target for participants to analyze is CodeGate.sys.

VM Image Download : https://codegate2025-qual.s3.ap-northeast-2.amazonaws.com/Windows11.7z
VM 7z Password : e011f1e26dfaccf6d090d9eec715a3b1eee26934c8ca17d203fcb99e1fafc7b3
To set up the challenge, you need to place the unzipped Windows11.qcow2 file under the share directory.

Hash

sha256 : b6a5c5d92a0d5f61f530bf66f1e7d43dc68b50cfd1d69b07921b326e1b46788f Windows11.7z

sha256 : 2ffc7da9e81da9cf0986abd92b4d35bf43742c706aa9bbbc6a9e060da46b7b6d  Windows11.qcow2

sha256 : f74562cd9628e543b0efe0b34d7e4d89100c9764777c290be022439044c14234  CodeGate.sys

sha256 : 2d14f3313d1ffe525da53c8d6595613cec8467bd51dc1ff7d6e7d2df4c11233f  LaunchAppContainer.exe
## How To Setup Docker
```
docker compose up -d
```

## How to Setup Debug
We highly recommend loading this driver into Vmware, VirtualBox or Hyper-V to debug and analyze it.
QEMU is just a use for CTF environment.

#### SetUp Debug Enviroment
This command must be executed with Windows Administrator privileges.
```
bcdedit /set testsigning on
bcdedit /set debug on
```
#### Load Drier
This command must be executed with Windows Administrator privileges.
```
sc create codegate binpath=/path/to/challenge.sys
sc start codegate
```

## Challenge Enviroment
The driver was developed in `Windows 11 242 26100.3476`. It also runs on the same version of the Exploit target server.
However, the intended solution is not significantly affected by the Windows version.
QEMU VMs operate in a 2-core, 2GB environment.

### Send Exploit
exploit.exe must be less than 200 kb.
```
python3 pow_client.py /path/to/exploit.exe
```

