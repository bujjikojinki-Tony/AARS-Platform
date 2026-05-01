import { Canvas, loadImage } from '../node_modules/@oai/artifact-tool/node_modules/skia-canvas/lib/index.mjs';
const cols=5, rows=3, tw=384, th=216, gap=18, pad=24;
const canvas=new Canvas(cols*tw+(cols-1)*gap+pad*2, rows*th+(rows-1)*gap+pad*2);
const ctx=canvas.getContext('2d');
ctx.fillStyle='#F1F5F9'; ctx.fillRect(0,0,canvas.width,canvas.height);
for(let i=1;i<=15;i++){
  const img=await loadImage(`scratch/previews/slide-${String(i).padStart(2,'0')}.png`);
  const c=(i-1)%cols, r=Math.floor((i-1)/cols);
  const x=pad+c*(tw+gap), y=pad+r*(th+gap);
  ctx.fillStyle='#FFFFFF'; ctx.fillRect(x-2,y-2,tw+4,th+4);
  ctx.drawImage(img,x,y,tw,th);
  ctx.fillStyle='rgba(15,23,42,.8)'; ctx.fillRect(x,y,42,26);
  ctx.fillStyle='#fff'; ctx.font='16px Arial'; ctx.fillText(String(i),x+12,y+18);
}
await canvas.toFile('scratch/previews/montage.png');
