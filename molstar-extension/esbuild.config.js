import { argv } from 'node:process';
import * as esbuild from 'esbuild';
import {sassPlugin} from 'esbuild-sass-plugin'

const
  productionMode = ('development' !== (argv[2] || process.env.NODE_ENV)),
  target = 'chrome100,firefox100,safari15'.split(',');

console.log(`${ productionMode ? 'production' : 'development' } build`);

const buildSCSS = await esbuild.context({
// TODO: change
  entryPoints: [ 'node_modules/molstar/lib/mol-plugin-ui/skin/blue.scss' ],
  bundle: true,
  target,
  // external: ['/images/*'],
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
  // options: https://www.npmjs.com/package/esbuild-sass-plugin

  // try local-css option

});

// bundle CSS
// const buildCSS = await esbuild.context({

//   entryPoints: [ './src/css/main.css' ],
//   bundle: true,
//   target,
//   external: ['/images/*'],
//   loader: {
//     '.png': 'file',
//     '.jpg': 'file',
//     '.svg': 'dataurl'
//   },
//   logLevel: productionMode ? 'error' : 'info',
//   minify: productionMode,
//   sourcemap: !productionMode && 'linked',
//   outdir: './build/css'

// });


// bundle JS
const buildTS = await esbuild.context({

  entryPoints: [ 'src/apps/viewer/app.ts' ],
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
  // await buildCSS.rebuild();
  // buildCSS.dispose();

  await buildTS.rebuild();
  buildTS.dispose();

}
else {

  // watch for file changes
  // await buildCSS.watch();
  await buildTS.watch();
  await buildSCSS.watch();

  // development server
  await buildSCSS.serve({
    servedir: './build'
  });

}
