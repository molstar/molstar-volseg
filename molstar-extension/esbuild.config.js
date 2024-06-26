import { argv } from 'node:process';
import * as esbuild from 'esbuild';
import { sassPlugin } from 'esbuild-sass-plugin'
import copyStaticFiles from 'esbuild-copy-static-files';
import { dtsPlugin } from 'esbuild-plugin-d.ts'

const
  productionMode = ('development' !== (argv[2] || process.env.NODE_ENV)),
  target = 'chrome100,firefox100,safari15'.split(',');

console.log(`${productionMode ? 'production' : 'development'} build`);

const staticLib = {
  src: './src',
  dest: './lib',
}

const staticLibCJS = {
  src: './src',
  dest: './lib/commonjs',
}

const buildLib = await esbuild.context({
  entryPoints: ['src/**/*.ts'],
  bundle: false,
  minify: false,
  sourcemap: true,
  outdir: './lib',
  platform: 'browser',
  tsconfig: 'tsconfig.json',
  plugins: [copyStaticFiles(staticLib), dtsPlugin()]
})

const buildLibCJS = await esbuild.context({
  entryPoints: ['src/**/*.ts'],
  bundle: false,
  minify: false,
  sourcemap: true,
  outdir: './lib/commonjs',
  platform: 'node',
  tsconfig: 'tsconfig.commonjs.json',
  plugins: [copyStaticFiles(staticLibCJS), dtsPlugin()]
})

const buildCSS = await esbuild.context({
  entryPoints: ['src/viewer/main.css'],
  bundle: true,
  target,
  loader: {
    '.png': 'file',
    '.jpg': 'file',
    '.svg': 'dataurl'
  },
  logLevel: productionMode ? 'error' : 'info',
  minify: true,
  sourcemap: !productionMode && 'linked',
  plugins: [sassPlugin()],
  outfile: './build/molstar.css'
});

// bundle TS
const buildTS = await esbuild.context({

  entryPoints: ['src/viewer/app.ts'],
  format: "esm",
  bundle: true,
  target,
  loader: {
    '.png': 'file',
    '.jpg': 'file',
    '.svg': 'dataurl'
  },
  drop: productionMode ? ['debugger', 'console'] : [],
  logLevel: productionMode ? 'error' : 'info',
  minify: productionMode,
  sourcemap: !productionMode && 'linked',
  // outdir: './build/js',
  outfile: './build/molstar.mjs',
  platform: 'browser',
  tsconfig: 'tsconfig.json'
});


if (productionMode) {

  // single production build
  await buildCSS.rebuild();
  buildCSS.dispose();

  await buildTS.rebuild();
  buildTS.dispose();

  await buildLib.rebuild();
  buildLib.dispose();

  await buildLibCJS.rebuild();
  buildLibCJS.dispose();
}
else {

  // watch for file changes
  await buildTS.watch();
  await buildCSS.watch();

  // development server
  await buildCSS.serve({
    servedir: './build'
  });

}
