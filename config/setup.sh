#/bin/bash
nfdc register /test udp://10.0.0.1
nfdc register /test udp://10.0.0.2
nfdc register /test udp://10.0.0.4
nfdc register /test udp://10.0.0.5
nfdc register /ndn/broadcast udp://10.0.0.1
nfdc register /ndn/broadcast udp://10.0.0.2
nfdc register /ndn/broadcast udp://10.0.0.4
nfdc register /ndn/broadcast udp://10.0.0.5
nfdc set-strategy /ndn/broadcast /localhost/nfd/strategy/multicast
nfdc set-strategy /test /localhost/nfd/strategy/access
#nfdc create -P udp://10.0.0.1
#nfdc create -P udp://10.0.0.2
#nfdc create -P udp://10.0.0.4
#nfdc create -P udp://10.0.0.5
