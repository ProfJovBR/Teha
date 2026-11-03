import {build} from 'esbuild';import {cp,mkdir} from 'node:fs/promises';
const url=process.env.SUPABASE_URL,key=process.env.SUPABASE_PUBLISHABLE_KEY;if(!url||!key)throw Error('Configure as variáveis Supabase.');
await mkdir('dist',{recursive:true});await cp('public','dist',{recursive:true});
await build({entryPoints:['src/app.js'],bundle:true,format:'iife',target:'es2022',outfile:'dist/app.js',minify:true,define:{__SUPABASE_URL__:JSON.stringify(url),__SUPABASE_KEY__:JSON.stringify(key)}});
