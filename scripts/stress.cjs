'use strict';
const assert = require('node:assert/strict');
const { Worker } = require('node:worker_threads');

async function main() {
  // Keep old and new backing stores alive together, while allocating and
  // releasing differently sized buffers. Check contents, not merely length.
  const retained = [];
  for (let i = 0; i < 64; i++) retained.push(Buffer.alloc(1024 * 1024, i));
  for (const size of [256, 8192, 128 * 1024, 4 * 1024 * 1024]) {
    let last;
    for (let i = 0; i < Math.min(10000, Math.ceil(256 * 1024 * 1024 / size)); i++) {
      last = Buffer.alloc(size, i & 255);
      assert.equal(last[0], i & 255);
      assert.equal(last[size - 1], i & 255);
    }
    assert(last);
  }
  for (let i = 0; i < retained.length; i++) {
    assert.equal(retained[i][0], i);
    assert.equal(retained[i][retained[i].length - 1], i);
  }
  // Backing stores may move between isolates; transferred ownership must
  // remain correct while the receiving isolate repeatedly allocates.
  const worker = new Worker(`
    const { parentPort } = require('node:worker_threads');
    const assert = require('node:assert/strict');
    parentPort.on('message', (buffer) => {
      const view = new Uint8Array(buffer);
      for (let i = 0; i < 4096; i++) Buffer.alloc(32768, i & 255);
      assert.equal(view[0], 123);
      assert.equal(view[view.length - 1], 123);
      parentPort.postMessage(buffer, [buffer]);
    });
  `, { eval: true });
  try {
    const input = new ArrayBuffer(4 * 1024 * 1024);
    new Uint8Array(input).fill(123);
    const result = new Promise((resolve, reject) => {
      worker.once('message', resolve);
      worker.once('error', reject);
      worker.once('exit', (code) => reject(new Error(`Worker exited: ${code}`)));
    });
    worker.postMessage(input, [input]);
    assert.equal(input.byteLength, 0);
    const returned = new Uint8Array(await result);
    assert.equal(returned.byteLength, 4 * 1024 * 1024);
    assert.equal(returned[0], 123);
    assert.equal(returned[returned.length - 1], 123);
  } finally {
    await worker.terminate();
  }
  console.log('PASS: retained backing stores, allocation sizes, worker transfer');
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
