import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dir = join(root, 'figures');
const d = JSON.parse(
  await readFile(join(root, 'results/classical-results.json'), 'utf8'),
);
if (
  d.configuration.version !== 3 ||
  d.runs.length !== 5 ||
  d.configuration.train_n !== 500000
)
  throw new Error('Complete full classical study required');
const ink = '#172033',
  blue = '#002fa7',
  orange = '#a94924',
  gray = '#697386';
const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
const txt = (x, y, s, size = 38, extra = '') =>
  `<text x="${x}" y="${y}" font-size="${size}" ${extra}>${s}</text>`;
const line = (x1, y1, x2, y2, color = '#dce0e6', extra = '') =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="2" ${extra}/>`;
const dot = (x, y, r, color, extra = '') =>
  `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}" ${extra}/>`;
const svg = (h, b) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="${h}" viewBox="0 0 720 ${h}"><rect width="720" height="${h}" fill="white"/><g font-family="Arial,sans-serif" fill="${ink}">${b}</g></svg>`;

const pts = d.runs.flatMap((r) => r.calibration.bins);
const cap =
  Math.ceil(Math.max(...pts.flatMap((x) => [x.prediction, x.expected])) / 50) *
  50;
const cx = (v) => 125 + (v / cap) * 525,
  cy = (v) => 640 - (v / cap) * 460;
let b =
  txt(30, 55, 'First check: ordinary customers', 40) +
  txt(30, 112, 'One fitted BG/NBD + Gamma-Gamma', 34);
for (let v = 0; v <= cap; v += 50) {
  b +=
    line(cx(0), cy(v), cx(cap), cy(v)) +
    txt(108, cy(v) + 11, v, 34, 'text-anchor="end"') +
    txt(cx(v), 685, v, 34, 'text-anchor="middle"');
}
b += line(cx(0), cy(0), cx(cap), cy(cap), gray, 'stroke-dasharray="8 7"');
pts.forEach(
  (p) =>
    (b += dot(
      cx(p.prediction),
      cy(p.expected),
      4,
      blue,
      'fill-opacity="0.22"',
    )),
);
for (let i = 0; i < 10; i++) {
  const x = mean(d.runs.map((r) => r.calibration.bins[i].prediction)),
    y = mean(d.runs.map((r) => r.calibration.bins[i].expected));
  b += dot(cx(x), cy(y), 8, blue);
}
b +=
  txt(390, 745, 'Predicted future value ($)', 36, 'text-anchor="middle"') +
  txt(
    34,
    410,
    'Expected future value ($)',
    36,
    'text-anchor="middle" transform="rotate(-90 34 410)"',
  ) +
  txt(30, 815, 'Large dots: mean of five model refits', 34) +
  txt(30, 865, 'Ten groups ranked by predicted LTV', 34);
const calibration = svg(905, b);

b =
  txt(30, 55, 'One forecast, two rebate durations', 38) +
  txt(30, 110, 'Future lift, dollars per customer', 34);
const fx = (v) => 85 + (v / 12) * 470;
const series = [
  [
    'LTV forecast: both durations',
    d.runs.map((r) => r.experiment.paired_score_effect),
    orange,
  ],
  ['True effect: rebate ends', d.runs.map(() => 0), gray],
  [
    'True effect: rebate continues',
    d.runs.map((r) => r.experiment.continuing.expected_effect),
    blue,
  ],
];
series.forEach(([label, values, color], i) => {
  const y = 220 + i * 155;
  b +=
    txt(30, y - 40, label, 38, `fill="${color}"`) +
    line(fx(0), y, fx(12), y) +
    line(fx(Math.min(...values)), y, fx(Math.max(...values)), y, color);
  values.forEach((v, j) => {
    b += dot(
      fx(v),
      y + (j - 2) * 5,
      7,
      color,
      'stroke="white" stroke-width="1"',
    );
  });
  b += txt(
    688,
    y + 14,
    mean(values).toFixed(2),
    42,
    `text-anchor="end" fill="${color}"`,
  );
});
for (const v of [0, 4, 8, 12])
  b += txt(fx(v), 620, v, 34, 'text-anchor="middle"');
b +=
  txt(30, 690, 'Same customers under both assignments', 34) +
  txt(30, 740, 'Dots: five complete model refits', 34);
const effects = svg(780, b);

b =
  txt(30, 55, 'Same RFM, different future value', 38) +
  txt(30, 111, 'Each pair shares its early history', 34);
const trials = d.runs.flatMap((r) => r.historical);
const maxX =
  Math.ceil(
    Math.max(...trials.map((t) => t.paired_early_monetary_change)) * 2,
  ) / 2;
const minX = Math.min(
  0,
  Math.floor(
    Math.min(...trials.map((t) => t.paired_early_monetary_change)) * 2,
  ) / 2,
);
const maxY = 25;
const hx = (v) => 125 + ((v - minX) / (maxX - minX)) * 525,
  hy = (v) => 650 - (v / maxY) * 450;
for (const v of [0, 5, 10, 15, 20, 25])
  b +=
    line(hx(minX), hy(v), hx(maxX), hy(v)) +
    txt(108, hy(v) + 11, v, 34, 'text-anchor="end"');
for (let v = minX; v <= maxX + 1e-6; v += 0.5)
  b += txt(hx(v), 695, v.toFixed(1), 34, 'text-anchor="middle"');
for (const t of trials) {
  b += line(
    hx(t.paired_early_monetary_change),
    hy(0),
    hx(t.paired_early_monetary_change),
    hy(t.continuing.expected_effect),
    '#dce0e6',
  );
  b += dot(hx(t.paired_early_monetary_change), hy(0), 6, orange);
  b += dot(
    hx(t.paired_early_monetary_change),
    hy(t.continuing.expected_effect),
    6,
    blue,
  );
}
b +=
  txt(385, 752, 'Change in mean order margin ($)', 36, 'text-anchor="middle"') +
  txt(
    34,
    435,
    'Future margin effect ($)',
    36,
    'text-anchor="middle" transform="rotate(-90 34 435)"',
  );
b +=
  dot(40, 814, 8, orange) +
  txt(64, 827, 'Rebate ends at week four', 36) +
  dot(40, 878, 8, blue) +
  txt(64, 891, 'Rebate continues', 36) +
  txt(30, 951, 'Five doses × five customer cohorts', 34);
const historical = svg(995, b);
for (const [name, source] of [
  ['classical-calibration', calibration],
  ['classical-effects', effects],
  ['classical-history', historical],
]) {
  await writeFile(join(dir, name + '.svg'), source);
  await sharp(Buffer.from(source))
    .resize({ width: 1440 })
    .png()
    .toFile(join(dir, name + '.png'));
}
console.log(
  JSON.stringify({
    figures: 3,
    refits: d.runs.length,
    meanPrediction: mean(d.runs.map((r) => r.calibration.prediction)),
    meanExpected: mean(d.runs.map((r) => r.calibration.expected)),
    scoreLift: mean(d.runs.map((r) => r.experiment.paired_score_effect)),
    trueContinuing: mean(
      d.runs.map((r) => r.experiment.continuing.expected_effect),
    ),
  }),
);
