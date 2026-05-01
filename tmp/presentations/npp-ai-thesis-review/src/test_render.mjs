import { Presentation, PresentationFile, column, text, fill, hug, drawSlideToCtx } from '@oai/artifact-tool';
import { Canvas } from '../node_modules/@oai/artifact-tool/node_modules/skia-canvas/lib/index.mjs';
const p=Presentation.create({slideSize:{width:1920,height:1080}});
const s=p.slides.add();
s.compose(column({width:fill,height:fill,padding:72,gap:20},[text('Hello', {width:fill,height:hug,style:{fontSize:80,bold:true,color:'#111'}})]),{frame:{left:0,top:0,width:1920,height:1080},baseUnit:8});
const blob=await PresentationFile.exportPptx(p); await blob.save('scratch/test.pptx');
const canvas=new Canvas(1920,1080); const ctx=canvas.getContext('2d');
console.log('slide keys', Object.keys(s));
try { await drawSlideToCtx(s,p,ctx); await canvas.toFile('scratch/test.png'); console.log('ok'); } catch(e) { console.error(e.stack); }
