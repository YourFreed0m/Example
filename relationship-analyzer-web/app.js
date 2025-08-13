(function(){
	'use strict';

	const storeKey = 'rel_analytics_data_v1';
	const state = loadState() || { events: [], answers: [] };

	function saveState(){ localStorage.setItem(storeKey, JSON.stringify(state)); }
	function loadState(){ try { return JSON.parse(localStorage.getItem(storeKey)||''); } catch(e){ return null; } }

	function fmtDate(ts){ const d=new Date(ts); return d.toLocaleString(); }
	function clamp01(v){ return Math.max(0, Math.min(1, v)); }

	// Tabs
	const tabs = document.querySelectorAll('.tab-btn');
	const views = document.querySelectorAll('[data-view]');
	tabs.forEach(btn=> btn.addEventListener('click', ()=> showView(btn.dataset.view)) );
	function showView(name){
		tabs.forEach(b=> b.classList.toggle('active', b.dataset.view===name));
		views.forEach(v=> v.classList.toggle('hidden', v.dataset.view!==name));
	}
	showView('events');

	// Events UI
	const elType = document.getElementById('event-type');
	const elIntensity = document.getElementById('event-intensity');
	const elNote = document.getElementById('event-note');
	const elAdd = document.getElementById('add-event');
	const elList = document.getElementById('events-list');

	// Tests UI
	const testsList = document.getElementById('tests-list');
	const testRunner = document.getElementById('test-runner');
	const backToTests = document.getElementById('back-to-tests');
	const testTitle = document.getElementById('test-title');
	const testForm = document.getElementById('test-form');
	const submitTest = document.getElementById('submit-test');

	// Dashboard UI
	const statHealth = document.getElementById('stat-health');
	const statStability = document.getElementById('stat-stability');
	const statConflicts = document.getElementById('stat-conflicts');
	const statResp = document.getElementById('stat-resp');
	const statCalm = document.getElementById('stat-calm');
	const llGrid = document.getElementById('ll-grid');

	// Test catalog
	const TESTS = {
		'happiness': {
			title: 'Насколько вы счастливы в отношениях',
			questions: [
				{ id:'happiness', text:'Насколько вы счастливы?', type:'scale', options:[0,0.25,0.5,0.75,1] },
				{ id:'satisfaction', text:'Удовлетворены качеством общения?', type:'scale', options:[0,0.25,0.5,0.75,1] },
			]
		},
		'conflict_style': {
			title: 'Стиль конфликта',
			questions: [
				{ id:'deescalate', text:'Вы склонны деэскалировать конфликт?', type:'scale', options:[0,0.25,0.5,0.75,1] },
				{ id:'criticize', text:'Вы часто критикуете партнёра?', type:'scale', options:[0,0.25,0.5,0.75,1] },
			]
		},
		'love_languages': {
			title: 'Языки любви (короткая форма)',
			questions: [
				{ id:'words_of_affirmation', text:'Слова поддержки', type:'scale', options:[0,1,2,3,4] },
				{ id:'quality_time', text:'Совместное время', type:'scale', options:[0,1,2,3,4] },
				{ id:'receiving_gifts', text:'Подарки', type:'scale', options:[0,1,2,3,4] },
				{ id:'acts_of_service', text:'Забота/помощь', type:'scale', options:[0,1,2,3,4] },
				{ id:'physical_touch', text:'Физический контакт', type:'scale', options:[0,1,2,3,4] },
			]
		}
	};

	function renderTestsList(){
		testsList.innerHTML='';
		Object.entries(TESTS).forEach(([key, test])=>{
			const card = document.createElement('div');
			card.className='card';
			card.innerHTML = `<h4>${test.title}</h4><div class="muted">${test.questions.length} вопросов</div><button data-test="${key}">Пройти</button>`;
			card.querySelector('button').addEventListener('click', ()=> startTest(key));
			testsList.appendChild(card);
		});
	}

	let currentTestKey = null;
	function startTest(key){
		currentTestKey = key;
		testTitle.textContent = TESTS[key].title;
		testForm.innerHTML = '';
		TESTS[key].questions.forEach(q=>{
			const wrap = document.createElement('div');
			wrap.className='question';
			wrap.innerHTML = `<div class="title">${q.text}</div>`;
			const opts = document.createElement('div');
			q.options.forEach((opt,i)=>{
				const id = `${key}-${q.id}-${i}`;
				const row = document.createElement('label');
				row.className='option';
				row.innerHTML = `<input type="radio" name="${q.id}" value="${opt}" id="${id}"><span>${opt}</span>`;
				opts.appendChild(row);
			});
			wrap.appendChild(opts);
			testForm.appendChild(wrap);
		});
		showView('test-runner');
	}

	backToTests.addEventListener('click', ()=> { showView('tests'); });

	submitTest.addEventListener('click', ()=>{
		if(!currentTestKey) return;
		const formData = new FormData(testForm);
		const payload = {};
		for(const q of TESTS[currentTestKey].questions){
			const raw = formData.get(q.id);
			if(raw===null){ alert('Заполните все вопросы'); return; }
			payload[q.id] = Number(raw);
		}
		// scoring
		let scored = payload;
		if(currentTestKey==='happiness'){
			const h = clamp01(Number(payload.happiness)||0);
			const s = clamp01(Number(payload.satisfaction)||0);
			scored = { happiness:h, satisfaction:s, composite: 0.6*h + 0.4*s };
		} else if(currentTestKey==='conflict_style'){
			const d = clamp01(Number(payload.deescalate)||0);
			const c = clamp01(Number(payload.criticize)||0);
			scored = { deescalate:d, criticize:c, composite: 0.6*d + 0.4*(1-c) };
		} else if(currentTestKey==='love_languages'){
			const sum = Object.values(payload).reduce((a,b)=>a+Number(b||0),0) || 1;
			scored = Object.fromEntries(Object.entries(payload).map(([k,v])=>[k, Number(v)/sum]));
		}
		state.answers.push({ questionnaire: currentTestKey, payload: scored, timestamp: new Date().toISOString() });
		saveState();
		updateDashboard();
		alert('Ответы сохранены');
		showView('tests');
	});

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

	// Analytics as before
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
		const neg = recent.filter(e=>['conflict','withdraw','criticisim','stonewall'].includes(e.type)).length;
		const total = recent.length; const stab = (pos - neg)/Math.max(1,total);
		return clamp01(0.5 + 0.5*stab);
	}

	function healthScore(){
		const pos = state.events.filter(e=>['positive','support','gift','date'].includes(e.type)).reduce((a,b)=>a+(b.intensity||0),0);
		const neg = state.events.filter(e=>['conflict','withdraw','criticisim','stonewall'].includes(e.type)).reduce((a,b)=>a+(b.intensity||0),0);
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
	renderTestsList();
	renderEvents();
	updateDashboard();
})();