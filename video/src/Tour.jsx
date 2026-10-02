// README tour: a terminal intro, the dashboard, a scroll through every category's
// newest English brief, and an outro. Shots come from `npm run capture`.
import React from "react";
import { AbsoluteFill, Easing, Img, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame } from "remotion";
import shots from "../public/shots/index.json";

export const FPS = 30;
const FADE = 6; // scenes cross-fade: each one fades in over the tail of the previous
const H = 720;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" };
const mono = { fontFamily: "var(--font-mono)", color: "var(--foreground)" };

const fontReady = delayRender("JetBrains Mono");
Promise.all([400, 700].map((w) => document.fonts.load(`${w} 24px "JetBrains Mono Variable"`)))
  .then(() => continueRender(fontReady));

const appear = (f, at) => ({ opacity: interpolate(f, [at, at + 8], [0, 1], clamp) });

const Cursor = () => {
  const f = useCurrentFrame();
  return (
    <span style={{ display: "inline-block", width: "0.55em", height: "1em", marginLeft: "0.15em",
      verticalAlign: "-0.12em", background: "var(--primary)", opacity: Math.floor(f / 15) % 2 }} />
  );
};

const Prompt = ({ text, start }) => {
  const f = useCurrentFrame();
  const typed = text.slice(0, Math.max(0, Math.floor((f - start) / 1.5)));
  return (
    <div><span style={{ color: "var(--primary)" }}>$ </span>{typed}{typed.length < text.length && <Cursor />}</div>
  );
};

const Terminal = ({ children }) => (
  <AbsoluteFill style={{ ...mono, justifyContent: "center", padding: "0 100px", fontSize: 30, lineHeight: 1.5 }}>
    {children}
  </AbsoluteFill>
);

const Label = ({ text, note }) => (
  <div style={{ ...mono, position: "absolute", left: 32, bottom: 32, fontSize: 24, padding: "10px 18px",
    background: "var(--card)", border: "1px solid var(--border)" }}>
    <span style={{ color: "var(--primary)" }}>$ open </span>{text}
    {note && <span style={{ color: "var(--muted-foreground)" }}>{"  "}{note}</span>}
  </div>
);

const Intro = () => {
  const f = useCurrentFrame();
  return (
    <Terminal>
      <Prompt text="ls ~/briefs" start={5} />
      <div style={{ fontSize: 24, color: "var(--muted-foreground)", display: "flex", flexWrap: "wrap", columnGap: 28, ...appear(f, 26) }}>
        {shots.map((s) => <span key={s.id}>{s.id}/</span>)}
      </div>
      <div style={{ fontSize: 76, fontWeight: 700, color: "var(--primary)", marginTop: 36, ...appear(f, 38) }}>
        Morning Briefs<Cursor />
      </div>
      <div style={{ fontSize: 26, color: "var(--muted-foreground)", ...appear(f, 50) }}>
        {shots.length} daily newsletters, written and fact-checked by Claude agents
      </div>
    </Terminal>
  );
};

const Dashboard = () => (
  <AbsoluteFill>
    <Img src={staticFile("shots/dashboard.png")} />
    <Label text="briefs.danieldeusing.de" />
  </AbsoluteFill>
);

const Brief = ({ shot, n }) => {
  const f = useCurrentFrame();
  // Two stops (masthead + TL;DR, then timeline + first sections) joined by a quick
  // slide: the GIF stores a held frame almost for free and a moving one in full.
  const y = interpolate(f, [45, 53], [0, -Math.min(shot.height - H, 800)], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "var(--background)" }}>
      <Img src={staticFile(shot.file)} style={{ position: "absolute", top: 0, left: 0, width: 1280, transform: `translateY(${y}px)` }} />
      <Label text={`~/briefs/${shot.id}`} note={`${n}/${shots.length}`} />
    </AbsoluteFill>
  );
};

const Outro = () => {
  const f = useCurrentFrame();
  return (
    <Terminal>
      <Prompt text="open https://briefs.danieldeusing.de" start={5} />
      <div style={{ fontSize: 24, color: "var(--muted-foreground)", marginTop: 12, ...appear(f, 64) }}>
        source: github.com/danieldeusing/morning-briefs-daniel<Cursor />
      </div>
    </Terminal>
  );
};

const scenes = [
  { dur: 90, el: <Intro /> },
  { dur: 75, el: <Dashboard /> },
  ...shots.map((shot, i) => ({ dur: 95, el: <Brief shot={shot} n={i + 1} /> })),
  { dur: 105, el: <Outro /> },
];

let at = 0;
const timeline = scenes.map((s) => {
  const from = at;
  at += s.dur - FADE;
  return { ...s, from };
});
export const DURATION = at + FADE;

// Every scene fades in over the one before it; the last one also fades out, so the
// looping GIF returns to the intro's blank terminal without a jump.
const Fade = ({ dur, out, children }) => {
  const f = useCurrentFrame();
  const opacity = interpolate(f, out ? [0, FADE, dur - FADE, dur] : [0, FADE], out ? [0, 1, 1, 0] : [0, 1], clamp);
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

export const Tour = () => (
  <AbsoluteFill style={{ background: "var(--background)" }}>
    {timeline.map(({ from, dur, el }, i) => (
      <Sequence key={i} from={from} durationInFrames={dur}>
        <Fade dur={dur} out={i === timeline.length - 1}>{el}</Fade>
      </Sequence>
    ))}
  </AbsoluteFill>
);
