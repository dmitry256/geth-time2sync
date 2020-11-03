#!/usr/bin/env python

import asyncio
from web3.auto import w3
import pandas as pd
import math
import time
import sys

async def produce_logs(q):
    previos_remaining_blocks = 0
    while True:
        remaining_blocks = w3.eth.syncing.highestBlock - w3.eth.syncing.currentBlock
        if previos_remaining_blocks != remaining_blocks:
            with open(sys.argv[1],'a') as log:
                current_time = int(time.time())
                log.write('%i %i\n' % (current_time, remaining_blocks))
                previos_remaining_blocks = remaining_blocks
                await q.put((current_time,remaining_blocks))
        await asyncio.sleep(5)

async def consume_logs(q):
    last_seen_blocks = 0
    last_seen_remaining_time = ''
    logs = pd.read_csv(sys.argv[1],sep=' ',names=['time','blocks'])
    logs.drop_duplicates(subset=['blocks'],keep='last',inplace=True)
    while True:
        # New block available
        new_time, new_blocks = await q.get()
        logs = logs.append({'time': new_time,'blocks': new_blocks}, ignore_index=True)

        # Recompute deltas
        logs['time_delta'] = logs.time - logs.time.shift(1)
        logs['blocks_delta'] = logs.blocks - logs.blocks.shift(1)

        # Filter delta time outliers
        min_time, max_time = logs.time_delta.quantile([0.05,0.95])
        logs = logs[(logs.time_delta > min_time) & (logs.time_delta < max_time)]

        # Block/time delta weighted averaged intervals
        time_delta_avg = (logs.time_delta * logs.blocks_delta).sum() / logs.blocks_delta.sum()
        blocks_delta_avg = (logs.blocks_delta * logs.time_delta).sum() / logs.time_delta.sum()

        # Out of sync blocks
        remaining_blocks = logs.blocks.iloc[-1]
        
        # Remaining days, hours and minutes
        delay_d = abs((remaining_blocks / blocks_delta_avg) * (time_delta_avg / 60 / 60 / 24))
        delay_h = abs(math.modf(delay_d)[0] * 24)
        delay_m = abs(math.modf(delay_h)[0] * 60)
        remaining_time = '%id,%ih,%im' % (delay_d,delay_h,delay_m)

        if last_seen_blocks != remaining_blocks:
            print('Blocks out of sync: %i' % remaining_blocks)
        if last_seen_remaining_time != remaining_time:
            print('Remaining time: %s' % remaining_time)

        last_seen_blocks = remaining_blocks
        last_seen_remaining_time = remaining_time

async def main():
    q = asyncio.Queue()
    await asyncio.gather(produce_logs(q), consume_logs(q))

asyncio.run(main())
