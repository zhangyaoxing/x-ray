#!/bin/bash
npx html-minifier-terser full.raw.html -o full.html \
  --collapse-whitespace --remove-comments --minify-js true --minify-css true
npx html-minifier-terser standard.raw.html -o standard.html \
  --collapse-whitespace --remove-comments --minify-js true --minify-css true
npx html-minifier-terser no-network.raw.html -o no-network.html \
  --collapse-whitespace --remove-comments --minify-js true --minify-css true