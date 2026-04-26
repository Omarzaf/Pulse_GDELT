import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SideNav } from "./SideNav";

describe("SideNav", () => {
  it("keeps exactly the three product navigation items", () => {
    render(<SideNav />);

    const nav = screen.getByRole("navigation", { name: "Primary" });
    const buttons = within(nav).getAllByRole("button");

    expect(buttons.map((button) => button.textContent)).toEqual([
      "World Dashboard",
      "Sources",
      "Time Series"
    ]);
    expect(buttons).toHaveLength(3);
  });
});
