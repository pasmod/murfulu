/** Mounts the app. Fonts are self-hosted, so nothing is fetched off the host. */

import "@fontsource-variable/inter";
import "./styles/farhang.css";
import "./styles/tokens.css";
import "./styles/base.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";

const root = document.getElementById("root");
if (!root) {
  throw new Error("no #root element to mount into");
}

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
