(function(){
	'use strict';
	const KEY='tg_clone_state_v1';
	const bc = ('BroadcastChannel' in self) ? new BroadcastChannel('tg-clone') : null;
	const state = load() || seed();
	function save(){ localStorage.setItem(KEY, JSON.stringify(state)); bc&&bc.postMessage({type:'sync'}); }
	function load(){ try{return JSON.parse(localStorage.getItem(KEY)||'');}catch(e){return null;} }
	function seed(){
		return {
			chats:[
				{id:'c1', title:'Алиса', pinned:false, muted:false, avatar:'A', messages:[
					{ id:'m1', from:'them', text:'Привет!', time:Date.now()-3600e3 },
					{ id:'m2', from:'me', text:'Привет 👋', time:Date.now()-3500e3 },
				]},
				{id:'c2', title:'Команда', pinned:true, muted:false, avatar:'K', messages:[
					{ id:'m1', from:'them', text:'Старт в 10:00', time:Date.now()-7200e3 },
				]},
			],
			active:null,
		};
	}

	// Elements
	const chatList = document.getElementById('chat-list');
	const search = document.getElementById('search');
	const titleEl = document.getElementById('chat-title');
	const msgList = document.getElementById('message-list');
	const input = document.getElementById('input');
	const sendBtn = document.getElementById('send');
	const replyPreview = document.getElementById('reply-preview');
	const pinChat = document.getElementById('pin-chat');
	const muteChat = document.getElementById('mute-chat');

	let replyTo = null;
	let editId = null;

	function fmtTime(t){ const d=new Date(t); return d.toLocaleTimeString().slice(0,5); }

	function currentChat(){ return state.chats.find(c=>c.id===state.active)||null; }

	function renderChats(filter=''){
		const q = filter.trim().toLowerCase();
		const items = state.chats.slice().sort((a,b)=> (b.pinned?-1:0) - (a.pinned?-1:0));
		chatList.innerHTML='';
		for(const c of items){
			if(q && !c.title.toLowerCase().includes(q)) continue;
			const last = c.messages[c.messages.length-1];
			const div = document.createElement('div');
			div.className='chat-item';
			div.dataset.id=c.id;
			div.innerHTML = `<div class="avatar">${c.avatar||c.title[0]||'?'}</div>
				<div class="meta"><div class="title">${c.title}${c.pinned?' 📌':''}${c.muted?' 🔕':''}</div><div class="last">${last? (last.from==='me'?'Вы: ':'')+last.text : 'Нет сообщений'}</div></div>`;
			div.addEventListener('click', ()=> { state.active=c.id; render(); });
			chatList.appendChild(div);
		}
	}

	function renderMessages(){
		const chat = currentChat();
		msgList.innerHTML='';
		if(!chat){ titleEl.textContent='Выберите чат'; return; }
		titleEl.textContent = chat.title;
		for(const m of chat.messages){
			const wrap = document.createElement('div');
			wrap.className = `msg ${m.from==='me'?'me':'them'}`;
			if(m.reply){
				const r = document.createElement('div'); r.className='reply'; r.textContent = m.reply.text.slice(0,120);
				wrap.appendChild(r);
			}
			const body = document.createElement('div'); body.textContent = m.text; wrap.appendChild(body);
			const bar = document.createElement('div'); bar.className='meta'; bar.textContent = fmtTime(m.time);
			wrap.appendChild(bar);
			const actions = document.createElement('div'); actions.className='actions';
			const btnReply = btn('Ответить', ()=>{ replyTo=m; showReply(); });
			const btnEdit = m.from==='me'? btn('Редактировать', ()=>{ editId=m.id; input.value=m.text; input.focus(); }) : null;
			const btnDel = m.from==='me'? btn('Удалить', ()=>{ removeMessage(chat.id, m.id); }) : null;
			actions.appendChild(btnReply);
			if(btnEdit) actions.appendChild(btnEdit);
			if(btnDel) actions.appendChild(btnDel);
			const reacts = document.createElement('div'); reacts.className='reactions';
			['👍','❤️','😂','😮','😢'].forEach(r=> reacts.appendChild(btn(r, ()=> addReaction(chat.id,m.id,r))));
			wrap.appendChild(reacts);
			wrap.appendChild(actions);
			msgList.appendChild(wrap);
		}
		msgList.scrollTop = msgList.scrollHeight;
	}

	function btn(label, fn){ const b=document.createElement('button'); b.textContent=label; b.addEventListener('click', (e)=>{ e.stopPropagation(); fn(); }); return b; }

	function showReply(){ if(replyTo){ replyPreview.classList.remove('hidden'); replyPreview.textContent = 'Ответ: '+ replyTo.text.slice(0,120); } else { replyPreview.classList.add('hidden'); replyPreview.textContent=''; } }

	function send(){
		const chat = currentChat(); if(!chat) return;
		const text = (input.value||'').trim(); if(!text) return;
		if(editId){
			const m = chat.messages.find(x=>x.id===editId); if(m){ m.text=text; m.time=Date.now(); }
			editId=null; input.value='';
			save(); renderMessages(); return;
		}
		const msg = { id: 'm'+Date.now(), from:'me', text, time: Date.now() };
		if(replyTo){ msg.reply = { id: replyTo.id, text: replyTo.text }; replyTo=null; showReply(); }
		chat.messages.push(msg);
		input.value='';
		save(); renderMessages();
	}

	function removeMessage(chatId, msgId){
		const chat = state.chats.find(c=>c.id===chatId); if(!chat) return;
		chat.messages = chat.messages.filter(m=>m.id!==msgId);
		save(); renderMessages();
	}

	function addReaction(chatId, msgId, emoji){
		// For simplicity, append emoji to text
		const chat = state.chats.find(c=>c.id===chatId); if(!chat) return;
		const m = chat.messages.find(m=>m.id===msgId); if(!m) return;
		m.text += ' '+emoji;
		save(); renderMessages();
	}

	pinChat.addEventListener('click', ()=>{ const c=currentChat(); if(c){ c.pinned=!c.pinned; save(); renderChats(search.value); }});
	muteChat.addEventListener('click', ()=>{ const c=currentChat(); if(c){ c.muted=!c.muted; save(); renderChats(search.value); }});
	search.addEventListener('input', ()=> renderChats(search.value));
	input.addEventListener('keydown', (e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }});
	sendBtn.addEventListener('click', send);
	if(bc){ bc.onmessage = (ev)=>{ if(ev.data&&ev.data.type==='sync'){ Object.assign(state, load()||state); render(); } }; }

	function render(){ renderChats(search.value); renderMessages(); }
	render();
})();