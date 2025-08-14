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

	// Word-based option sets
	const SETS = {
		freq5: ['никогда','редко','иногда','часто','всегда'],
		agree5: ['совсем нет','скорее нет','иногда','скорее да','да'],
		importance4: ['не важно','немного важно','важно','очень важно'],
		yn: ['нет','да'],
	};
	// Map option word -> numeric value in [0,1]
	const MAP = new Map([
		...SETS.freq5.map((w,i)=>[w, i/4]),
		...SETS.agree5.map((w,i)=>[w, i/4]),
		...SETS.importance4.map((w,i)=>[w, i/3]),
		['нет',0],['да',1],
	]);
	function optionToValue(word){ return MAP.has(word) ? MAP.get(word) : 0; }

	// Test catalog (simple wording, word-only answers)
	const TESTS = {
		'relationship_overview': {
			title: 'Общий тест отношений',
			questions: [
				{ id:'talk_daily', text:'Вы общаетесь каждый день?', scale:'freq5' },
				{ id:'trust', text:'Вы доверяете партнёру?', scale:'agree5' },
				{ id:'support', text:'Вы чувствуете поддержку?', scale:'agree5' },
				{ id:'respect', text:'В отношениях есть уважение?', scale:'agree5' },
				{ id:'boundaries', text:'Границы соблюдаются?', scale:'agree5' },
				{ id:'conflicts_rare', text:'Конфликты случаются редко?', scale:'agree5' },
				{ id:'apology', text:'Вы умеете извиняться?', scale:'agree5' },
				{ id:'forgive', text:'Вы умеете прощать?', scale:'agree5' },
				{ id:'gratitude', text:'Вы говорите «спасибо»?', scale:'freq5' },
				{ id:'plan_future', text:'Вы обсуждаете будущее?', scale:'freq5' },
				{ id:'time_together', text:'Вы проводите время вместе?', scale:'freq5' },
				{ id:'jealousy_low', text:'Ревности мало?', scale:'agree5' },
				{ id:'no_criticism', text:'Критики мало?', scale:'agree5' },
				{ id:'calm', text:'Вы сохраняете спокойствие в споре?', scale:'agree5' },
				{ id:'decisions', text:'Решения принимаете вместе?', scale:'agree5' },
				{ id:'chores_share', text:'Быт делите честно?', scale:'agree5' },
				{ id:'intimacy', text:'Близость вас устраивает?', scale:'agree5' },
				{ id:'money_talks', text:'Про деньги говорите спокойно?', scale:'agree5' },
				{ id:'humor', text:'Вы вместе смеётесь?', scale:'freq5' },
				{ id:'empathy', text:'Вы понимаете чувства друг друга?', scale:'agree5' },
				// Love languages inside overview
				{ id:'ll_words', text:'Слова поддержки важны?', scale:'importance4' },
				{ id:'ll_time', text:'Совместное время важно?', scale:'importance4' },
				{ id:'ll_gifts', text:'Подарки важны?', scale:'importance4' },
				{ id:'ll_service', text:'Забота важна?', scale:'importance4' },
				{ id:'ll_touch', text:'Контакт важен?', scale:'importance4' },
			]
		},
		'happiness': {
			title: 'Счастье в отношениях',
			questions: [
				{ id:'happiness', text:'Вы счастливы в отношениях?', scale:'agree5' },
				{ id:'satisfaction', text:'Вас устраивает общение?', scale:'agree5' },
			]
		},
		'conflict_style': {
			title: 'Стиль конфликта',
			questions: [
				{ id:'deescalate', text:'Вы умеете успокаивать спор?', scale:'agree5' },
				{ id:'criticize', text:'Вы часто критикуете?', scale:'agree5' },
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
			const options = SETS[q.scale] || SETS.agree5;
			options.forEach((label,i)=>{
				const id = `${key}-${q.id}-${i}`;
				const row = document.createElement('label');
				row.className='option';
				row.innerHTML = `<input type="radio" name="${q.id}" value="${label}" id="${id}"><span>${label}</span>`;
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
		const rawAnswers = {};
		for(const q of TESTS[currentTestKey].questions){
			const raw = formData.get(q.id);
			if(raw===null){ alert('Заполните все вопросы'); return; }
			rawAnswers[q.id] = String(raw);
		}
		// score mapping
		let scored = {};
		if(currentTestKey==='happiness'){
			const h = clamp01(optionToValue(rawAnswers.happiness));
			const s = clamp01(optionToValue(rawAnswers.satisfaction));
			scored = { happiness:h, satisfaction:s, composite: 0.6*h + 0.4*s };
		} else if(currentTestKey==='conflict_style'){
			const d = clamp01(optionToValue(rawAnswers.deescalate));
			const c = clamp01(optionToValue(rawAnswers.criticize));
			scored = { deescalate:d, criticize:c, composite: 0.6*d + 0.4*(1-c) };
		} else if(currentTestKey==='relationship_overview'){
			// Compute composite (invert negative items)
			const negIds = new Set(['criticize','jealousy_low']); // 'jealousy_low' is positive wording, so keep as is
			let sum = 0, n = 0;
			for(const q of TESTS[currentTestKey].questions){
				if(q.id.startsWith('ll_')) continue; // separate
				let v = clamp01(optionToValue(rawAnswers[q.id]));
				if(negIds.has(q.id)) v = 1 - v;
				sum += v; n++;
			}
			const composite = n? sum/n : 0.5;
			// Love languages
			const ll = {
				words_of_affirmation: optionToValue(rawAnswers.ll_words||'не важно'),
				quality_time: optionToValue(rawAnswers.ll_time||'не важно'),
				receiving_gifts: optionToValue(rawAnswers.ll_gifts||'не важно'),
				acts_of_service: optionToValue(rawAnswers.ll_service||'не важно'),
				physical_touch: optionToValue(rawAnswers.ll_touch||'не важно'),
			};
			const lls = Object.values(ll).reduce((a,b)=>a+b,0)||1;
			for(const k in ll){ ll[k] = ll[k]/lls; }
			scored = { composite, ...ll };
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

	// Analytics
	function computeLoveLanguages(){
		const langs = { words_of_affirmation:0, quality_time:0, receiving_gifts:0, acts_of_service:0, physical_touch:0 };
		const weights = { gift:'receiving_gifts', support:'acts_of_service', positive:'words_of_affirmation', date:'quality_time', touch:'physical_touch' };
		for(const e of state.events){ const key=weights[e.type]; if(key){ langs[key]+= (e.intensity||0); } }
		for(const a of state.answers){
			if(a.questionnaire==='love_languages' || a.questionnaire==='relationship_overview'){
				for(const k of Object.keys(langs)){
					if(a.payload[k]!=null){ langs[k] += Number(a.payload[k])||0; }
				}
			}
		}
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
		const lastOverview = [...state.answers].reverse().find(a=>a.questionnaire==='relationship_overview');
		if(lastOverview){ const c=Number(lastOverview.payload?.composite)||0.5; score = 0.6*score + 0.4*c; }
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