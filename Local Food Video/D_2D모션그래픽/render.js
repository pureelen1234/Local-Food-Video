#!/usr/bin/env node
/*
 * film.html 을 프레임 단위로 캡처해 MP4 로 인코딩한다.
 *   node render.js                       # 미리보기 (1280x720)
 *   node render.js --quality final       # 최종본 (1920x1080)
 *   node render.js --stills 4,12,30      # 지정 시점 정지 이미지(PNG)만 저장
 * 필요: Node.js, playwright(Chromium), ffmpeg (환경변수 FFMPEG 또는 PATH 또는 python imageio-ffmpeg)
 */
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const { chromium } = require('playwright');

const ROOT = __dirname;
const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : def; };

const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'config.json'), 'utf8'));
// 절대 규칙: 슬로건 문구 변경 금지 → 줄바꿈용 sloganLines 가 원문과 같은지 검사
const SLOGAN = '건강한 지역먹거리를 우리 식탁 위에';
if (cfg.labels.slogan !== SLOGAN || cfg.labels.sloganLines.join(' ') !== SLOGAN) {
  console.error('[중단] 슬로건 문구가 원문과 다릅니다: ' + cfg.labels.sloganLines.join(' '));
  process.exit(1);
}

function findFfmpeg() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  try { execSync('ffmpeg -version', { stdio: 'ignore' }); return 'ffmpeg'; } catch (e) {}
  try { return execSync('python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"').toString().trim(); } catch (e) {}
  throw new Error('ffmpeg 를 찾을 수 없습니다 (brew install ffmpeg 또는 pip install imageio-ffmpeg)');
}

(async () => {
  const quality = opt('quality', 'preview');
  const out = cfg.output[quality];
  if (!out) throw new Error('알 수 없는 quality: ' + quality);
  const fps = cfg.fps;

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: out.width, height: out.height } });
  await page.goto('file://' + path.join(ROOT, 'film.html'));
  const info = await page.evaluate(c => window.init(c), cfg);
  await page.evaluate(async () => {
    await Promise.all([400, 700, 800].map(w => document.fonts.load(`${w} 40px "Noto Sans KR"`, '가나다ABC123')));
    await document.fonts.ready;
  });
  const fontOk = await page.evaluate(() => document.fonts.check('800 40px "Noto Sans KR"', '건강한 지역먹거리'));
  console.log(`총 길이 ${info.total}s, 장면 ${info.scenes.length}개, 한글 폰트 로드: ${fontOk ? 'OK' : '실패'}`);
  if (!fontOk) { await browser.close(); process.exit(1); }

  const stills = opt('stills', null);
  if (stills) {
    const dir = path.join(ROOT, 'output', 'stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const s of stills.split(',').map(Number)) {
      await page.evaluate(t => window.renderAt(t), s);
      const file = path.join(dir, `still_${s.toFixed(1).padStart(4, '0')}s.png`);
      await page.screenshot({ path: file });
      console.log('저장:', file);
    }
    await browser.close();
    return;
  }

  const file = path.join(ROOT, out.file);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const total = Math.round(info.total * fps);
  const ff = spawn(findFfmpeg(), ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', quality === 'final' ? '18' : '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', file],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg 종료코드 ' + c)))));
  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.renderAt(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (fps * 5) === 0) process.stdout.write(`\r${(i / fps).toFixed(0)}s / ${info.total}s  (${((Date.now() - t0) / 1000).toFixed(0)}초 경과)`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
  console.log(`\n완료: ${file}`);
})().catch(e => { console.error(e); process.exit(1); });
