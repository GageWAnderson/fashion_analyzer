import { type UIColorTheme } from "~/styles/themes"

export const LIGHT_THEME: UIColorTheme = {
  colors: {
    primary: "#4B9EFA",
    secondary: "#A6A6A9",
    accent: "#4B9EFA",
    neutral: "#F4F4F9",
    "base-100": "#E5E5E7",
    "base-200": "#67676B",
    "base-300": "#232326",
    info: "#00CDFF",
    success: "#009256",
    warning: "#e0a500",
    error: "#FC444C",
  },
  extendedClasses: {
    ".info-vibrant-cyan": {
      "background-color": "rgb(0, 241, 255)",
      color: "#232326 !important",
    },
    ".info-yellow-green": {
      "background-color": "rgb(139, 201, 0)",
      color: "#232326 !important",
    },
  },
}
