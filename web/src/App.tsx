/**
 * The routes.
 *
 * One route per screen in `shell/screens.ts`, so a screen cannot appear in the
 * menu without a page behind it. A screen with no component yet gets the
 * placeholder, which says what it is for and which task builds it.
 */

import type React from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { Placeholder } from "./screens/Placeholder";
import { Affixes } from "./screens/affixes/Affixes";
import { Build } from "./screens/build/Build";
import { Compound } from "./screens/compound/Compound";
import { Corpus } from "./screens/corpus/Corpus";
import { Explain } from "./screens/explain/Explain";
import { Questions } from "./screens/questions/Questions";
import { Rules } from "./screens/rules/Rules";
import { Search } from "./screens/search/Search";
import { Word } from "./screens/word/Word";
import { SCREENS } from "./shell/screens";
import { Shell } from "./shell/Shell";

/** Screens that are built. Everything else is still a placeholder. */
const BUILT: Record<string, () => React.ReactElement> = {
  "/": Search,
  "/word/:wordId": Word,
  "/build": Build,
  "/compound": Compound,
  "/affixes": Affixes,
  "/explain": Explain,
  "/rules": Rules,
  "/corpus": Corpus,
  "/questions": Questions,
};

export function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        {SCREENS.map((screen) => {
          const Built = BUILT[screen.path];
          return (
            <Route
              key={screen.path}
              path={screen.path}
              element={Built ? <Built /> : <Placeholder screen={screen} />}
            />
          );
        })}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
