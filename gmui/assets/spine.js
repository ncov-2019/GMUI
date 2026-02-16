let spinePlayer = null;

function ready(skelname, atlasname, animationname, setalpha) {
	try {
		const playerConfig = {
			alpha: true,// 透明度
			premultipliedAlpha: setalpha,
			antialias: true,//抗锯齿
			autoResize: true,
			backgroundColor: "#00000000",
			showControls: false,
			debug: false,
			success: function (player) {
				const skeletonData = player;
				skeletonData.defaultMix = 0.3;
				onPlayerLoaded(animationname);
			},
			transitionTime: 0.3,
			error: onPlayerError,
		};

		if (skelname.endsWith('.skel')) {
			playerConfig.skelUrl = skelname;
		} else if (skelname.endsWith('.json')) {
			playerConfig.jsonUrl = skelname;
		}
		playerConfig.atlasUrl = atlasname;
		if (animationname !== false) playerConfig.animation = animationname;
		// 初始化播放器
		spinePlayer = new spine.SpinePlayer("player-container", playerConfig);
	} catch (e) {
		console.error("加载失败", e);
		nonono();
	}
}

// 加载成功
function onPlayerLoaded(n) {
	window.spineReady = true;
	if (n === false) {
		const animNames = getname();
		if (spinePlayer.setAnimation) {
			spinePlayer.setAnimation(animNames[0], true);
		} else if (spinePlayer.animationState) {
			spinePlayer.animationState.setAnimation(0, animNames[0], true);
		}
		spinePlayer.paused = false;
		spinePlayer.visible = true;
		if (spinePlayer.update) spinePlayer.update(0);

	}
	setTimeout(() => {
		hideAndRemoveHamood();
	}, 1000);
}

// 加载失败
function onPlayerError(message) {
	console.error("动画资源加载失败:", message);
	nonono();
}

function hideAndRemoveHamood() {
	const hamoodElement = document.getElementById('Hamood');
	hamoodElement.style.opacity = 0;
	setTimeout(() => {
		hamoodElement.remove();
		const playerContainer = document.getElementById('player-container');
		playerContainer.style.opacity = 1;
	}, 210);
}

function nonono() {
	const hamoodElement = document.getElementById('Hamood');
	if (hamoodElement) {
		hamoodElement.classList.remove('loading');
		hamoodElement.classList.add('error');
	}
}

function border(n) {
	const outline = document.querySelector('.outline');
	outline.classList.toggle('active', n === 1);
	const el = document.getElementById('lyrics');
	el.classList.toggle('active', n === 1);
	if (n === 1 && el.textContent.trim().length === 0) {
		el.innerHTML = '&nbsp;';
	}
}

// ========== 核心动画控制 ==========
// 播放
function play(animString) {
	const state = spinePlayer.animationState;
	playremove();
	const anims = animString.split(',');
	if (anims.length === 0) {
		return;
	}
	state.setAnimation(0, anims[0], true);
	for (let i = 1; i < anims.length; i++) {
		const isLoop = (i === anims.length - 1);
		state.addAnimation(0, anims[i], isLoop, 0);
	}
}

// playtrack(动画名称, 数字循环次数-无此项则默认播放1次,0则循环);
function playtrack(animName, loopCount, trackIndex) {
	const state = spinePlayer.animationState;
	const track = trackIndex !== undefined ? trackIndex : getAvailableTrackIndex();
	const anims = animName.split(',');
	if (loopCount === 0) {
		if (anims.length === 1) {
			state.setAnimation(track, animName, true);
		} else {
			for (let i = 0; i < anims.length; i++) {
				const anim = anims[i];
				const isLoop = (i === anims.length - 1);
				if (i === 0) {
					state.setAnimation(track, anim, isLoop);
				} else {
					state.addAnimation(track, anim, isLoop, 0);
				}
			}
		}
	} else if (loopCount === 1) {
		for (let i = 0; i < anims.length; i++) {
			const anim = anims[i];
			const isLoop = (i === anims.length - 1);
			if (i === 0) {
				state.setAnimation(track, anim, isLoop);
			} else {
				state.addAnimation(track, anim, isLoop, 0);
			}
		}
	} else if (loopCount > 1) {
		let loopCounter = 0;
		for (let i = 0; i < anims.length; i++) {
			const anim = anims[i];
			if (i === anims.length - 1) {
				const trackEntry = state.setAnimation(track, anim, false);
				trackEntry.listener = {
					complete: function (entry) {
						loopCounter++;
						if (loopCounter < loopCount) {
							state.addAnimation(track, anim, false, 0);
						} else {
							state.clearTrack(track);
						}
					}
				};
			} else {
				if (i === 0) {
					state.setAnimation(track, anim, false);
				} else {
					state.addAnimation(track, anim, false, 0);
				}
			}
		}
	}
}

// 清空所有轨道的动画
function playremove() {
	const state = spinePlayer.animationState;

	for (let i = 1; i < 100; i++) {
		if (state.getCurrent(i) !== null) {
			state.setEmptyAnimation(i, 0.2);
		} else {
			if (i > state.tracks.length) break;
		}
	}
	state.update(0);
	if (spinePlayer?.requestRender) {
		spinePlayer.requestRender();
	}
}

// 获取可用的多轨
function getAvailableTrackIndex() {
	if (!spinePlayer?.animationState) return 1;

	const state = spinePlayer.animationState;
	let trackIndex = 1;

	while (state.tracks[trackIndex]?.animation) {
		trackIndex++;
	}
	return trackIndex;
}

// 设置透明度
function setopacity(opacity) {
	const validOpacity = Math.min(1, Math.max(0, Number(opacity) || 0));
	document.documentElement.style.opacity = validOpacity;
}

// 设置位置
function setposition(x, y) {
	const targetX = Number(x) || 0;
	const targetY = Number(y) || 0;
	spinePlayer.skeleton.x = targetX * spinePlayer.skeleton.scaleY;
	spinePlayer.skeleton.y = targetY * spinePlayer.skeleton.scaleY;
}

// 设置缩放
function setscale(value, x, y) {
	const clampedValue = Math.min(10, Math.max(0.01, value));
	const skeleton = spinePlayer.skeleton;
	const targetX = Number(x) || 0;
	const targetY = Number(y) || 0;

	skeleton.scaleX = clampedValue;
	skeleton.scaleY = clampedValue;
	skeleton.x = targetX * clampedValue;
	skeleton.y = targetY * clampedValue;
}

// 返回name1,name2,name3...
function getname() {
	const skeletonData = spinePlayer.skeleton?.data;
	const animations = skeletonData.animations;
	const names = animations.map(anim => anim.name);
	return names;
}


// 获取插槽名返回name1,name2,name3...
function getslotname() {
	const skeleton = spinePlayer?.skeleton;
	if (!skeleton || !skeleton.data?.slots) {
		return [];
	}
	const names = skeleton.data.slots.map(slotData => slotData.name);
	return names.sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
}


// 隐藏/显示某个插槽
function setslot(slotName, state) {
	const skeleton = spinePlayer?.skeleton;
	const slot = skeleton.findSlot(slotName);
	let shouldShow;
	if (state === 0 || state === 1) {
		shouldShow = (state === 1);
	} else {
		shouldShow = slot.color.a <= 0.001;
	}
	if (shouldShow) {
		slot._forceHidden = false;
		slot.color.a = 1;
	} else {
		slot._forceHidden = true;
		slot.color.a = 0;
	}

	if (spinePlayer?.requestRender) {
		spinePlayer.requestRender();
	}
}

// 透明度检测
function transparentpixel(x, y) {
	const canvas = document.elementFromPoint(x, y);
	if (!canvas || canvas.tagName !== 'CANVAS') return false;
	const rect = canvas.getBoundingClientRect();
	const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
	if (!gl) return false;
	const pixel = new Uint8Array(4);
	gl.readPixels(
		x - rect.left,
		canvas.height - (y - rect.top) - 1,
		1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel
	);
	console.error(pixel[3] < 10);
	return pixel[3] < 10;
}

let url = null;

function seturl(n) {
	url = n;
}


// ========== 音频控制 ==========
// 播放和台词
let l={},i=0,t=null,f='',s=[],d={};
function parseLyrics(t){
    d={};
    const m=/\[music:([^\]]+)\](.*?)(?=\[music:|$)/gs;
    let a;
    while((a=m.exec(t))!==null){
        const n=a[1],c=a[2].replace(/^[,\n\r]+/,''),r=[];
        const e=/\[(\d{2}):(\d{2})\.(\d{2,3})\]([^^,]+)(?:\^|,|$)/g;
        let l;
        while((l=e.exec(c))!==null){
            const m=parseInt(l[1]),e=parseInt(l[2]),n=l[3].length===2?parseInt(l[3])*10:parseInt(l[3]),o=l[4].trim();
            if(o)r.push({time:m*60+e+n/1000,text:o});
        }
        r.sort((a,b)=>a.time-b.time);
        r.length>0&&(d[n]=r);
    }
    if(!Object.keys(d).length){
        const r=[];
        const e=/\[(\d{2}):(\d{2})\.(\d{2,3})\]([^^,]+)(?:\^|,|$)/g;
        let l;
        while((l=e.exec(t))!==null){
            const m=parseInt(l[1]),e=parseInt(l[2]),n=l[3].length===2?parseInt(l[3])*10:parseInt(l[3]),o=l[4].trim();
            if(o)r.push({time:m*60+e+n/1000,text:o});
        }
        r.sort((a,b)=>a.time-b.time);
        r.length>0&&(d.default=r);
    }
}
// 更新台词
function updateLyricDisplay(){
    if(!window.audioPlayer||!window.audioPlayer.currentAudio)return t&&(clearInterval(t),t=null),void 0;
    const c=window.audioPlayer.currentAudio.currentTime,e=document.getElementById('lyrics'),a=window.audioPlayer.currentAudio;
    const n=a.ended||a.duration&&c>=a.duration-0.1||!window.audioPlayer.isPlaying;
    if(n&&!window.audioPlayer.audioQueue.length)return e.style.setProperty('--lo','0'),s=[],i=-1,t&&(clearInterval(t),t=null),void 0;
    if(!s.length){
        const t=a.src.split('/').pop().split('?')[0],l=t.split('.')[0],o=[t,l];
        for(const r of o)if(d[r]){s=d[r];i=-1;break}
        !s.length&&d.default&&(s=d.default,i=-1);
    }
    if(!s.length)return e.style.setProperty('--lo','0'),void 0;
    if(n)return e.style.setProperty('--lo','0'),i=-1,void 0;
    if(s.length===1){
        const t=s[0];
        c>=t.time&&!n?(e.innerHTML!==t.text||e.style.getPropertyValue('--lo')==='0')&&(e.innerHTML=t.text,e.style.setProperty('--lo','var(--li)'),i=0):(e.style.setProperty('--lo','0'),i=-1);
        return;
    }
    let l=-1;
    for(let t=s.length-1;t>=0;t--)if(c>=s[t].time-0.5){l=t;break}
    l>=0&&l!==i?(e.innerHTML=s[l].text,e.style.setProperty('--lo','var(--li)'),i=l):l===-1&&i!==-1&&(e.style.setProperty('--lo','0'),i=-1);
}
// 台词
function setlyrics(c){
    t&&(clearInterval(t),t=null);
    s=[];i=-1;
    const e=document.getElementById('lyrics');
    e.style.setProperty('--lo','0');e.innerHTML='&nbsp;';
    parseLyrics(c);
    updateLyricDisplay();
    t=setInterval(updateLyricDisplay,1000);
}
const o=window.audiosequence;
window.audiosequence=function(){
    s=[];i=-1;
    const t=document.getElementById('lyrics');
    t.style.setProperty('--lo','0');t.innerHTML='&nbsp;';
    return o.apply(this,arguments);
};
if(window.audioPlayer){
    const t=window.playaudio;
    window.playaudio=function(a){
        s=[];i=-1;
        const c=document.getElementById('lyrics');
        c.style.setProperty('--lo','0');c.innerHTML='&nbsp;';
        return t.apply(this,arguments);
    };
}
function setupAudioListener(a){
    a._lyricsListenerAdded||(a.addEventListener('loadeddata',()=>{s=[];i=-1}),a._lyricsListenerAdded=true);
}
function playaudio(c){
    window.audioPlayer||(window.audioPlayer={currentAudio:null,audioQueue:[],isPlaying:false});
    s=[];i=-1;
    const e=document.getElementById('lyrics');
    e.style.setProperty('--lo','0');t&&(clearInterval(t),t=null);
    window.audioPlayer.isPlaying = false;
    if(window.audioPlayer.currentAudio){
        window.audioPlayer.currentAudio.pause();
        window.audioPlayer.currentAudio.currentTime=0;
    }
    window.audioPlayer.audioQueue=[];
    const a=c.split(',').map(t=>t.trim());
    if(a.length===1){
        const t=new Audio(`${url}${a[0]}`);
        setupAudioListener(t);
        window.audioPlayer.currentAudio=t;
        window.audioPlayer.isPlaying = true;
        window.audioPlayer.currentAudio.play();
    }else{
        a.forEach(t=>window.audioPlayer.audioQueue.push(`${url}${t}`));
        audiosequence();
    }
    updateLyricDisplay();
    t=setInterval(updateLyricDisplay,1000);
}
function audiosequence(){
    if(!window.audioPlayer||!window.audioPlayer.audioQueue.length)return window.audioPlayer.isPlaying=false,t&&(clearInterval(t),t=null),void 0;
    window.audioPlayer.isPlaying=true;
    if(window.audioPlayer.currentAudio){
        window.audioPlayer.currentAudio.pause();
        window.audioPlayer.currentAudio.currentTime=0;
    }
    const c=window.audioPlayer.audioQueue.shift(),e=new Audio(c);
    setupAudioListener(e);
    window.audioPlayer.currentAudio=e;
    window.audioPlayer.currentAudio.onended=audiosequence;
    window.audioPlayer.currentAudio.onerror=()=>audiosequence();
    window.audioPlayer.currentAudio.play().catch(()=>audiosequence());
}

function lyricsmove(x, y) {
	const el = document.getElementById('lyrics');
	const topPercent = Math.max(0, Math.min(100, -y / 2 + 50));
	const leftPercent = Math.max(0, Math.min(100, x / 2 + 50));
	el.style.top = `${topPercent}%`;
	el.style.left = `${leftPercent}%`;
}

function lyricsscale(scale) {
	const el = document.getElementById('lyrics');
	const safeScale = Math.max(0.01, Math.min(5, scale));
	el.style.transform = `translate(-50%, -50%) scale(${safeScale})`;
}

function lyricsopacity(opacity) {
	const safeOpacity = Math.max(0, Math.min(1, parseFloat(opacity))).toFixed(2);
	document.documentElement.style.setProperty('--li', safeOpacity);
}

window.addEventListener('DOMContentLoaded', () => {
	window.htmlReady = true;
});
