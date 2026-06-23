import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextVitals,
  ...nextTs,
  {
    ignores: [".next/**", "out/**", "build/**", "test-results/**", "playwright-report/**", "next-env.d.ts", "**/*.cjs"],
  },
];

export default eslintConfig;
