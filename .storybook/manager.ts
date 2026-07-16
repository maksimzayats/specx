import { addons } from "@storybook/manager-api"
import { create } from "@storybook/theming/create"

addons.setConfig({
  navSize: 230,
  toolbar: {
    copy: { hidden: true },
    eject: { hidden: true },
    fullscreen: { hidden: true },
  },
  sidebar: {
    showRoots: true,
    collapsedRoots: [],
  },
  theme: create({
    base: "light",
    brandTitle: "Specx",
    brandImage: "./logo-storybook.svg",
    brandUrl: "https://github.com/maksimzayats/specx",
    brandTarget: "_self",
    colorPrimary: "#3a10e5",
    colorSecondary: "#585c6d",
    appBg: "#ffffff",
    appContentBg: "#ffffff",
    appPreviewBg: "#ffffff",
    appBorderColor: "#ededed",
    appBorderRadius: 6,
    barBg: "#ffffff",
    barTextColor: "#6e6e80",
    fontBase:
      'ui-sans-serif, -apple-system, system-ui, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif',
    fontCode:
      'ui-monospace, "SFMono-Regular", "SF Mono", Menlo, Monaco, Consolas, monospace',
  }),
})
