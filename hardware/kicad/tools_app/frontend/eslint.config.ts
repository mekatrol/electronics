import process from 'node:process'

import type { ESLint, Linter } from 'eslint'
import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import pluginOxlint from 'eslint-plugin-oxlint'
import skipFormatting from 'eslint-config-prettier/flat'

import requireFilenameCase from './eslint-rules/requireFilenameCase.js'

const localPlugin = {
  rules: {
    requireFilenameCase,
  },
} as unknown as ESLint.Plugin

const sharedRules: Linter.RulesRecord = {
  'local/requireFilenameCase': 'error',
  'prefer-promise-reject-errors': 'error',
  'max-len': ['error', 200, { ignorePattern: '^\\s*\\/' }],
  quotes: ['error', 'single', { avoidEscape: true, allowTemplateLiterals: false }],
  '@typescript-eslint/no-var-requires': 'off',
  'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
  'no-console': [
    process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    { allow: ['warn', 'error'] },
  ],
  'no-unused-vars': 'off',
  'no-var': 'error',
  'no-restricted-imports': [
    'error',
    {
      patterns: [
        {
          group: ['../**'],
          message:
            "Alias import '@' must be used for imports from outside the current directory. Same-directory './' imports are allowed.",
        },
      ],
    },
  ],
  'prefer-arrow-callback': 'error',
  'func-style': ['error', 'expression', { allowArrowFunctions: true }],
  '@typescript-eslint/no-unused-vars': [
    'error',
    {
      argsIgnorePattern: '^_.*$',
      varsIgnorePattern: '^_$',
      caughtErrorsIgnorePattern: '^_$',
    },
  ],
  '@typescript-eslint/explicit-function-return-type': [
    'error',
    {
      allowExpressions: true,
      allowHigherOrderFunctions: true,
      allowTypedFunctionExpressions: true,
    },
  ],
}

const vueRules: Linter.RulesRecord = {
  ...sharedRules,
  'vue/html-closing-bracket-newline': 'off',
  'vue/html-self-closing': 'off',
  'vue/max-attributes-per-line': 'off',
  'vue/singleline-html-element-content-newline': 'off',
  'vue/block-order': ['error', { order: ['template', 'script', 'style'] }],
}

// To allow more languages other than `ts` in `.vue` files, uncomment the following lines:
// import { configureVueProject } from '@vue/eslint-config-typescript'
// configureVueProject({ scriptLangs: ['ts', 'tsx'] })
// More info at https://github.com/vuejs/eslint-config-typescript/#advanced-setup

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{vue,ts,mts,tsx}'],
  },

  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

  ...pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,

  {
    plugins: {
      local: localPlugin,
    },
  },

  {
    files: ['**/*.ts'],
    rules: sharedRules,
  },

  {
    files: ['**/*.vue'],
    rules: vueRules,
  },

  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/__tests__/*'],
  },

  ...pluginOxlint.buildFromOxlintConfigFile('.oxlintrc.json'),

  skipFormatting,
)
