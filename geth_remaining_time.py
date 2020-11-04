#!/usr/bin/env python

import asyncio
from web3.auto import w3
import pandas as pd
import math
import time
import sys

async def produce_logs(q,last_seen_block=0):
    previos_remaining_blocks = last_seen_block
    while True:
        state = w3.eth.syncing
        remaining_blocks = state.highestBlock - state.currentBlock
        if previos_remaining_blocks != remaining_blocks:
            with open(sys.argv[1],'a') as log:
                now = int(time.time())
                log.write('%i %i\n' % (now,remaining_blocks))
                previos_remaining_blocks = remaining_blocks
                await q.put((now, remaining_blocks))
        await asyncio.sleep(5)

async def consume_logs(q,logs):
    last_seen_blocks = 0
    last_seen_remaining_time = ''
    # Delay is classified as outlier when it excceds the boundaries
    max_time = logs.time_delta.quantile(0.95)
    while True:
        # New block available
        new_time, new_blocks = await q.get()
        new_time_delta = new_time - logs.time.iloc[-1]
        new_event = {
                'time': new_time,
                'blocks': new_blocks,
                'time_delta': new_time_delta,
                'blocks_delta': new_blocks - logs.blocks.iloc[-1],
                }
        logs = logs.append(new_event, ignore_index=True)

        print(('\nSynchronisation took longer than expected: %s'
                if new_time_delta > max_time else '\nNew entry: %s') % new_event)

        # Filter delta time outliers
        logs = logs[logs.time_delta < max_time]

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
    logs = pd.read_csv(sys.argv[1],sep=' ',names=['time','blocks'])
    logs.drop_duplicates(subset=['blocks'],keep='last',inplace=True)
    logs['time_delta'] = logs.time - logs.time.shift(1)
    logs['blocks_delta'] = logs.blocks - logs.blocks.shift(1)
    await asyncio.gather(produce_logs(q,logs.blocks.iloc[-1]), consume_logs(q,logs))

if __name__ == '__main__':
    asyncio.run(main())
