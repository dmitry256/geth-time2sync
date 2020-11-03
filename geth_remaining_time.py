#!/usr/bin/env python

import asyncio
from web3.auto import w3
import pandas as pd
import math
import time
import sys

async def log_remaining_blocks(q):
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

async def poll_delays(q):
    last_seen_blocks = 0
    last_seen_remaining_time = ''
    logs = pd.read_csv(sys.argv[1],sep=' ',names=['time','val'])
    while True:
        # New info available
        new_time, new_blocks = await q.get()
        logs = logs.append({'time': new_time,'val': new_blocks},ignore_index=True)
        
        # Recompute deltas
        logs['time_delta'] = logs.time - logs.time.shift(1)
        logs['val_delta'] = logs.val - logs.val.shift(1)

        # Filter delta time outliers, skip last value
        min_time, max_time = logs.time_delta.quantile([0.01,0.99])
        logs = logs[(logs.time_delta < max_time)
                & (logs.time_delta > min_time)]

        time_delta_avg, val_delta_avg = logs.time_delta.mean(), logs.val_delta.mean()

        # Out of sync blocks
        blocks = logs.val.iloc[-1]
        
        # Remaining days, hours and minutes
        delay_d = (blocks / val_delta_avg) * (time_delta_avg / 60 / 60 / 24)
        delay_h = math.modf(delay_d)[0] * 24
        delay_m = math.modf(delay_h)[0] * 60
        remaining_time = '%sd,%sh,%sm' % (abs(int(delay_d)),abs(int(delay_h)),abs(int(delay_m)))

        if last_seen_blocks != blocks: print('Blocks out of sync: %i' % blocks)
        if last_seen_remaining_time != remaining_time: print('Remaining time: %s' % remaining_time)

        last_seen_blocks = blocks
        last_seen_remaining_time = remaining_time

async def main():
    q = asyncio.Queue()
    await asyncio.gather(log_remaining_blocks(q), poll_delays(q))

asyncio.run(main())
