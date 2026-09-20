const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('utils/browser_storage_component/index.html', 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const values = new Map();
const replies = [];
let receive;
const parent = { postMessage: (data, origin) => replies.push({ data, origin }) };
vm.runInNewContext(script, {
  window: {
    parent,
    location: { origin: 'http://localhost:8520' },
    addEventListener: (name, callback) => { receive = callback; },
  },
  localStorage: {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  },
});

function event(overrides = {}) {
  return {
    source: parent, origin: 'http://localhost:8520',
    data: { type: 'streamlit:render', args: {
      action: 'set', storage_key: 'local-rag:settings', value: '{"top_k":3}',
    } },
    ...overrides,
  };
}

receive(event({ source: {} }));
receive(event({ origin: 'https://example.invalid' }));
receive(event({ data: null }));
receive(event({ data: { type: 'streamlit:render', args: { action: 'set', storage_key: 'unrelated', value: 'test' } } }));
assert.equal(values.size, 0);
receive(event());
assert.equal(values.get('local-rag:settings'), '{"top_k":3}');
receive(event({ data: { type: 'streamlit:render', args: { action: 'get', storage_key: 'local-rag:settings' } } }));
assert.equal(replies.at(-1).data.value.value, '{"top_k":3}');
assert.ok(replies.every(reply => reply.origin === 'http://localhost:8520'));
console.log('Browser storage provenance and legitimate round-trip checks passed.');
