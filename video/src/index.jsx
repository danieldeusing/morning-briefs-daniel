import React from "react";
import { Composition, registerRoot } from "remotion";
import "@danieldeusing/design/tokens.css";
import "@fontsource-variable/jetbrains-mono";
import { DURATION, FPS, Tour } from "./Tour";

registerRoot(() => (
  <Composition id="Tour" component={Tour} durationInFrames={DURATION} fps={FPS} width={1280} height={720} />
));
