const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/node_modules/'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  // Transform ES modules from react-markdown and related packages
  transformIgnorePatterns: [
    'node_modules/(?!(react-markdown|remark-gfm|rehype-sanitize|unified|bail|is-plain-obj|trough|vfile|unist-util-stringify-position|micromark|decode-named-character-reference|character-entities|property-information|hast-util-whitespace|space-separated-tokens|comma-separated-tokens|pretty-bytes|remark-parse|remark-rehype|rehype-react|mdast-util-to-hast|mdast-util-definitions|unist-util-visit|unist-util-visit-parents|unist-util-is|unist-util-position|mdast-util-from-markdown|mdast-util-to-string|micromark-util-chunked|micromark-util-classify-character|micromark-util-combine-extensions|micromark-util-character|micromark-util-decode-numeric-character-reference|micromark-util-encode|micromark-util-normalize-identifier|micromark-util-resolve-all|micromark-util-sanitize-uri|micromark-util-subtokenize|micromark-util-symbol|micromark-util-types|micromark-extension-gfm|micromark-extension-gfm-autolink-literal|micromark-extension-gfm-footnote|micromark-extension-gfm-strikethrough|micromark-extension-gfm-table|micromark-extension-gfm-tagfilter|micromark-extension-gfm-task-list-item|ccount|escape-string-regexp|markdown-table)/)',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
