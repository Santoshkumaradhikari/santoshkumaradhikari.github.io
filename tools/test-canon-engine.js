#!/usr/bin/env node
/* Runs the published Canon Score 1.6.0 test cases against the website's
   JavaScript engine (investors-canon/js/canon-engine.js):
       node tools/test-canon-engine.js
   Every case must give the same answer as the Python reference calculation. */
var path = require('path'), fs = require('fs');
var E = require(path.join(__dirname, '..', 'investors-canon', 'js', 'canon-engine.js'));
var cases = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'investors-canon', 'data', 'canon-score-test-cases-v1.6.0.json'), 'utf8')).cases;
var bad = 0;
cases.forEach(function (c) {
  var got = E[c.function](c.inputs);
  var ok = JSON.stringify(got) === JSON.stringify(c.expected);
  if (!ok) { bad++; console.log('FAIL', c.id, c.function, 'expected', JSON.stringify(c.expected), 'got', JSON.stringify(got)); }
});
console.log((cases.length - bad) + ' of ' + cases.length + ' cases pass');
process.exit(bad ? 1 : 0);
