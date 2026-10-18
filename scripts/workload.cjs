'use strict';
const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const kind = process.argv[2];
const start = performance.now();
let checksum = 0;
let operations;
if (kind === 'buffer-churn' || kind === 'buffer-retained') {
  operations = 40000;
  const retained = new Array(kind === 'buffer-retained' ? 256 : 1);
  for (let i = 0; i < operations; i++) {
    const value = Buffer.alloc(32768, i & 255);
    retained[i % retained.length] = value;
    checksum += value[0];
  }
  assert.equal(checksum, 5093856);
  assert.equal(retained[(operations - 1) % retained.length][0], 63);
} else if (kind === 'heap-churn') {
  operations = 5000000;
  const retained = new Array(10000);
  for (let i = 0; i < operations; i++) {
    retained[i % retained.length] = { index: i, data: [i, i + 1, i + 2] };
    checksum += retained[i % retained.length].data[0];
  }
  assert.equal(checksum, operations * (operations - 1) / 2);
} else {
  throw new Error(`Unknown workload: ${kind}`);
}
const seconds = (performance.now() - start) / 1000;
console.log(JSON.stringify({ kind, operations, seconds, ops: operations / seconds,
  maxRssKiB: process.resourceUsage().maxRSS, memory: process.memoryUsage(), checksum }));
