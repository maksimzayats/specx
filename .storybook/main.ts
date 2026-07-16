import type { StorybookConfig } from "@storybook/react-vite"
import path from "path"
import remarkGfm from "remark-gfm"

const config: StorybookConfig = {
  stories: ["../docs/**/*.mdx"],
  addons: [
    "@storybook/addon-links",
    {
      name: "@storybook/addon-docs",
      options: {
        mdxPluginOptions: {
          mdxCompileOptions: {
            remarkPlugins: [remarkGfm],
          },
        },
      },
    },
    {
      name: "@storybook/addon-essentials",
      options: {
        actions: false,
        backgrounds: false,
        measure: false,
        outline: false,
        toolbars: false,
        viewport: false,
      },
    },
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
  staticDirs: ["../public"],
  async viteFinal(finalConfig) {
    finalConfig.resolve = finalConfig.resolve || { alias: {} }
    finalConfig.resolve.alias = {
      ...finalConfig.resolve.alias,
      "@storybookComponents": path.resolve(__dirname, "./components/"),
    }

    return finalConfig
  },
}

export default config
