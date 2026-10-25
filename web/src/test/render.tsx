/** Rendering a screen the way the app does: inside the router and the shell. */

import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import { App } from "../App";

/** One component, with a router around it. */
export function renderWithRouter(ui: ReactElement, route = "/") {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);
}

/** The whole app, at one route. */
export function renderApp(route = "/") {
  return renderWithRouter(<App />, route);
}
