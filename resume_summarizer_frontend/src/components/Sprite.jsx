// Pixel sprites drawn from text grids. One character per pixel; "." is transparent.
export const PALETTE = {
  k: "#000000", n: "#1d2b53", p: "#7e2553", g: "#008751", b: "#ab5236", d: "#5f574f",
  l: "#c2c3c7", w: "#fff1e8", r: "#ff004d", o: "#ffa300", y: "#ffec27", G: "#00e436",
  B: "#29adff", v: "#83769c", P: "#ff77a8", s: "#ffccaa",
};

export const SPRITES = {
  hero: [
    ".....kkkkkk.....",
    "....kbbbbbbk....",
    "...kbbbbbbbbk...",
    "...kbssssssbk...",
    "...kskssssksk...",
    "...kssssssssk...",
    "....ksspppsk....",
    ".....kssssk.....",
    "...kkBBBBBBkk...",
    "..kBBBwwwwBBBk..",
    "..ksBBwkkwBBsk..",
    "..ksBBwwwwBBsk..",
    "...kBBwkkwBBk...",
    "...kddkkkkddk...",
    "...kddk..kddk...",
    "...kkk....kkk...",
  ],
  slime: [
    "....kkkk....",
    "..kkGGGGkk..",
    ".kGGwGGGGGk.",
    ".kGwwGGGGGk.",
    "kGGGGGGGGGGk",
    "kGGkGGGGkGGk",
    "kGGkGGGGkGGk",
    "kGGGGGGGGGGk",
    "kgGGGGGGGGgk",
    ".kkkkkkkkkk.",
  ],
  lock: [
    "...kkkk...",
    "..kk..kk..",
    "..k....k..",
    ".kkkkkkkk.",
    ".kooooook.",
    ".kookkook.",
    ".kookkook.",
    ".koookook.",
    ".kooooook.",
    ".kkkkkkkk.",
  ],
  gem: [
    "..kkkk..",
    ".kwccck.",
    "kwccccck",
    "kcccccck",
    ".kcccck.",
    "..kcck..",
    "...kk...",
  ],
  scroll: [
    ".kkkkkkkkkk.",
    "kwwwwwwwwwwk",
    ".kwwwwwwwwk.",
    ".kwkkkkkkwk.",
    ".kwwwwwwwwk.",
    ".kwkkkkkwwk.",
    ".kwwwwwwwwk.",
    ".kwkkkkkkwk.",
    "kwwwwwwwwwwk",
    ".kkkkkkkkkk.",
  ],
  cloud: [
    "......wwww........",
    "....wwwwwwww......",
    "..wwwwwwwwwwwwww..",
    ".wwwwwwwwwwwwwwww.",
    "wwwwwwwwwwwwwwwwww",
    ".llwwwwwwwwwwwwll.",
  ],
};

export function Sprite({ name, scale = 4, color = PALETTE.B, title, className = "" }) {
  const rows = SPRITES[name];
  const width = rows[0].length;
  const rects = [];
  rows.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      if (ch === ".") return;
      const fill = ch === "c" ? color : PALETTE[ch];
      rects.push(<rect key={`${x}-${y}`} x={x} y={y} width="1" height="1" fill={fill} />);
    });
  });
  return (
    <svg
      className={`sprite ${className}`}
      viewBox={`0 0 ${width} ${rows.length}`}
      width={width * scale}
      height={rows.length * scale}
      shapeRendering="crispEdges"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
    >
      {title && <title>{title}</title>}
      {rects}
    </svg>
  );
}
