import { create, themes, type ThemeVars } from "@storybook/theming"

import type { Theme } from "./constants"

const fontBase =
  'ui-sans-serif, -apple-system, system-ui, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
const fontCode =
  '"JetBrains Mono", ui-monospace, "SFMono-Regular", "SF Mono", Menlo, Monaco, Consolas, monospace'

const light = create({
  base: "light",
  brandTitle: "Specx",
  brandImage: "./logo-storybook.svg",
  brandUrl: "https://github.com/maksimzayats/specx",
  brandTarget: "_self",
  fontBase,
  fontCode,
  colorPrimary: "#3a10e5",
  colorSecondary: "#585c6d",
  appBg: "#ffffff",
  appContentBg: "#ffffff",
  appPreviewBg: "#ffffff",
  appBorderColor: "#ededed",
  appBorderRadius: 6,
  barBg: "#ffffff",
  barTextColor: "#6e6e80",
})

const dark = create({
  ...themes.dark,
  brandTitle: "Specx",
  brandImage: "./logo-storybook-dark.svg",
  brandUrl: "https://github.com/maksimzayats/specx",
  brandTarget: "_self",
  fontBase,
  fontCode,
  colorPrimary: "#3a10e5",
  colorSecondary: "#585c6d",
  appBg: "#212121",
  appContentBg: "#212121",
  appPreviewBg: "#212121",
  appBorderColor: "#393939",
  appBorderRadius: 6,
  barBg: "#212121",
  barTextColor: "#c1c1c1",
})

export const THEMES: Record<Theme, ThemeVars> = { light, dark }
