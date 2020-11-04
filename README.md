# geth-time2sync
Approximate time of full syncronisation on a given ethereum node

## Run the script and specify path to log

```bash
geth_remaining_time.py /mnt/media/ethereum/geth_remaining_blocks.log
```

## Sample output

```
New entry: {'time': 1604474176, 'blocks': 1408347, 'time_delta': 130, 'blocks_delta': -531}
Blocks out of sync: 1408347
Remaining time: 4d,1h,44m

New entry: {'time': 1604474271, 'blocks': 1407900, 'time_delta': 95, 'blocks_delta': -447}
Blocks out of sync: 1407900
Remaining time: 4d,1h,42m

New entry: {'time': 1604474462, 'blocks': 1407376, 'time_delta': 191, 'blocks_delta': -524}
Blocks out of sync: 1407376

New entry: {'time': 1604474592, 'blocks': 1406879, 'time_delta': 130, 'blocks_delta': -497}
Blocks out of sync: 1406879
Remaining time: 4d,1h,40m

Synchronisation took longer than expected: {'time': 160460447, 'blocks': 1569804, 'time_delta': 13001, 'blocks_delta': -1}
Blocks out of sync: 1406878
Remaining time: 4d,23h,270m
```
