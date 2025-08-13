(function(){
	'use strict';

	const storeKey = 'rel_analytics_data_v1';
	const state = loadState() || { events: [], answers: [] };

	function saveState(){ localStorage.setItem(storeKey, JSON.stringify(state)); }
	function loadState(){ try { return JSON.parse(localStorage.getItem(storeKey)||''); } catch(e){ return null; } }

	function fmtDate(ts){ const d=new Date(ts); return d.toLocaleString(); }

	// UI elements
	const elType = document.getElementById('event-type');
	const elIntensity = document.getElementById('event-intensity');
	const elNote = document.getElementById('event-note');
	const elAdd = document.getElementById('add-event');
	const elList = document.getElementById('events-list');

	const elQH = document.getElementById('q-happiness');
	const elQS = document.getElementById('q-satisfaction');
	const elSubmitH = document.getElementById('submit-happiness');

	const elLLW = document.getElementById('ll-words');
	const elLLT = document.getElementById('ll-time');
	const elLLG = document.getElementById('ll-gifts');
	const elLLS = document.getElementById('ll-service');
	const elLLP = document.getElementById('ll-touch');
	const elSubmitLL = document.getElementById('submit-ll');

	const statHealth = document.getElementById('stat-health');
	const statStability = document.getElementById('stat-stability');
	const statConflicts = document.getElementById('stat-conflicts');
	const statResp = document.getElementById('stat-resp');
	const statCalm = document.getElementById('stat-calm');
	const llGrid = document.getElementById('ll-grid');

	function addEvent(){
		const ev = {
			id: Date.now(),
			timestamp: new Date().toISOString(),
			type: elType.value,
			intensity: Number(elIntensity.value)||0,
			note: elNote.value||''
		};
		state.events.push(ev);
		saveState();
		renderEvents();
		updateDashboard();
		elNote.value='';
	}

	function renderEvents(){
		elList.innerHTML = '';
		const items = state.events.slice().sort((a,b)=>new Date(b.timestamp)-new Date(a.timestamp));
		for(const e of items){
			const div = document.createElement('div');
			div.className='event-item';
			const cls = (e.type==='conflict'?'neg':'pos');
			div.innerHTML = `<div><div class="etype ${cls}">${e.type}</div><div class="muted">${fmtDate(e.timestamp)}</div></div><div>${e.intensity}</div><div>${e.note||''}</div>`;
			elList.appendChild(div);
		}
	}

	function submitHappiness(){
		const ans = {
			questionnaire: 'happiness',
			payload: {
				happiness: clamp01(Number(elQH.value)||0),
				satisfaction: clamp01(Number(elQS.value)||0)
			},
			timestamp: new Date().toISOString()
		};
		state.answers.push(ans);
		saveState();
		updateDashboard();
	}

	function submitLoveLanguages(){
		const vals = {
			words_of_affirmation: Number(elLLW.value)||0,
			quality_time: Number(elLLT.value)||0,
			receiving_gifts: Number(elLLG.value)||0,
			acts_of_service: Number(elLLS.value)||0,
			physical_touch: Number(elLLP.value)||0,
		};
		const sum = Object.values(vals).reduce((a,b)=>a+b,0) || 1;
		const norm = Object.fromEntries(Object.entries(vals).map(([k,v])=>[k, v/sum]));
		state.answers.push({ questionnaire: 'love_languages', payload: norm, timestamp: new Date().toISOString() });
		saveState();
		updateDashboard();
	}

	function clamp01(v){ return Math.max(0, Math.min(1, v)); }

	// Analytics
	function computeLoveLanguages(){
		const langs = { words_of_affirmation:0, quality_time:0, receiving_gifts:0, acts_of_service:0, physical_touch:0 };
		const weights = { gift:'receiving_gifts', support:'acts_of_service', positive:'words_of_affirmation', date:'quality_time', touch:'physical_touch' };
		for(const e of state.events){ const key=weights[e.type]; if(key){ langs[key]+= (e.intensity||0); } }
		for(const a of state.answers){ if(a.questionnaire==='love_languages'){ for(const [k,v] of Object.entries(a.payload||{})){ if(k in langs){ langs[k]+=Number(v)||0; } } } }
		const total = Object.values(langs).reduce((a,b)=>a+b,0) || 1;
		for(const k in langs){ langs[k] = langs[k]/total; }
		return langs;
	}

	function computeBalances(){
		const resp={}, calm={}; let conflicts=0, total=0;
		for(const e of state.events){
			total++;
			if(e.type==='apology'){ resp['_a']=(resp['_a']||0)+1; }
			if(e.type==='conflict'){ conflicts++; }
			if(e.type==='calm'){ calm['_a']=(calm['_a']||0)+1; }
		}
		function balance(d){ const vals=Object.values(d); if(!vals.length) return 0; if(vals.length===1) return 1; const s=vals.sort((a,b)=>a-b); const a=s[s.length-1], b=s[s.length-2]; const denom=(a+b)||1; return (a-b)/denom; }
		return { responsibility: balance(resp), calmness: balance(calm), conflictFreq: (conflicts/Math.max(1,total)) };
	}

	function rollingStability(days=30){
		if(!state.events.length) return 0.5;
		const now=Date.now(); const start= now - days*86400*1000;
		const recent = state.events.filter(e=> new Date(e.timestamp).getTime()>=start);
		if(!recent.length) return 0.5;
		const pos = recent.filter(e=>['positive','support','date','gift'].includes(e.type)).length;
		const neg = recent.filter(e=>['conflict','withdraw','criticism','stonewall'].includes(e.type)).length;
		const total = recent.length; const stab = (pos - neg)/Math.max(1,total);
		return clamp01(0.5 + 0.5*stab);
	}

	function healthScore(){
		const pos = state.events.filter(e=>['positive','support','gift','date'].includes(e.type)).reduce((a,b)=>a+(b.intensity||0),0);
		const neg = state.events.filter(e=>['conflict','withdraw','criticism','stonewall'].includes(e.type)).reduce((a,b)=>a+(b.intensity||0),0);
		let score = 0.5 + Math.max(-10, Math.min(10, pos-neg))/20;
		const lastHappy = [...state.answers].reverse().find(a=>a.questionnaire==='happiness');
		if(lastHappy){ const h=Number(lastHappy.payload?.happiness)||0.5; score = 0.7*score + 0.3*h; }
		return clamp01(score);
	}

	function updateDashboard(){
		const langs = computeLoveLanguages();
		const balances = computeBalances();
		const stability = rollingStability();
		const health = healthScore();
		statHealth.textContent = (health*100).toFixed(0)+'%';
		statStability.textContent = (stability*100).toFixed(0)+'%';
		statConflicts.textContent = (balances.conflictFreq*100).toFixed(0)+'%';
		statResp.textContent = balances.responsibility.toFixed(2);
		statCalm.textContent = balances.calmness.toFixed(2);
		llGrid.innerHTML = '';
		for(const [k,v] of Object.entries(langs)){
			const wrap = document.createElement('div');
			wrap.className='ll-item';
			wrap.innerHTML = `<div>${k}</div><div class="bar" style="width:${(v*100).toFixed(0)}%"></div>`;
			llGrid.appendChild(wrap);
		}
	}

	// Wire
	elAdd.addEventListener('click', addEvent);
	elSubmitH.addEventListener('click', submitHappiness);
	elSubmitLL.addEventListener('click', submitLoveLanguages);

	// Init
	renderEvents();
	updateDashboard();
})();