import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const source = JSON.parse(
  await readFile(join(root, "results/meta-holdouts.json"), "utf8"),
);
const example = source.rows.find((row) => row.holdout === 1);
const rows = [
  ["Observed effect", example.actual, "#172033"],
  ["Two-stage prediction", example.two_stage, "#002fa7"],
  ["Direct prediction", example.direct, "#a94924"],
];
const x = (v) => 100 + ((v + 0.15) / 0.5) * 405;
const text = (x, y, label, size = 38, extra = "") =>
  `<text x="${x}" y="${y}" font-size="${size}" ${extra}>${label}</text>`;
const line = (x1, y1, x2, y2, color = "#dce0e6", extra = "") =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="2" ${extra}/>`;
let body =
  text(30, 60, "One held-out experiment", 42) +
  text(30, 115, "Reported effects (%)", 36);
rows.forEach(([label, value, color], i) => {
  const y = 245 + i * 155;
  body +=
    text(30, y - 42, label, 40, `fill="${color}"`) +
    line(x(-0.15), y, x(0.35), y) +
    line(x(0), y - 24, x(0), y + 24, "#697386", 'stroke-dasharray="6 5"') +
    `<circle cx="${x(value)}" cy="${y}" r="9" fill="${color}"/>` +
    text(
      696,
      y + 14,
      `${value >= 0 ? "+" : ""}${value.toFixed(3)}%`,
      40,
      `fill="${color}" text-anchor="end"`,
    );
});
for (const tick of [-0.1, 0, 0.1, 0.2, 0.3])
  body += text(
    x(tick),
    640,
    `${tick > 0 ? "+" : ""}${tick.toFixed(1)}`,
    32,
    'text-anchor="middle"',
  );
body += text(30, 710, "Day et al. · Table 4 · Feed Holdout 1", 32);
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="750" viewBox="0 0 720 750"><rect width="720" height="750" fill="white"/><g font-family="Arial,sans-serif" fill="#172033">${body}</g></svg>`;
await writeFile(join(root, "figures/meta-holdout.svg"), svg);
await sharp(Buffer.from(svg))
  .resize({ width: 1440 })
  .png()
  .toFile(join(root, "figures/meta-holdout.png"));
console.log("Generated reported Table 4 holdout figure");
