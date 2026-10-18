"""Luma's learning interface. Retrieval and answer generation live in luma.runtime."""
import html
import streamlit as st
from luma.config import manifest_path
from luma.documents import load_documents
from luma.graph import feedback_reply
from luma.runtime import create_runtime, ask

st.set_page_config(page_title='Luma · Your learning space', page_icon='✳', layout='wide')
st.markdown('''
<style>
:root { --luma-ink:#172e38; --luma-teal:#087f75; }
.stApp { background:#f7f9f8; }
[data-testid="stMainBlockContainer"] { max-width:1080px; padding-top:2.6rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#edf3f1; border-right:1px solid #dae5e0; }
[data-testid="stSidebar"] h2 { font-size:1.05rem; color:#172e38; }
.luma-brand { font-size:1.9rem; font-weight:750; letter-spacing:-.07em; color:#172e38; margin-bottom:.3rem; }
.luma-brand span { color:#087f75; padding-right:.4rem; }
.luma-eyebrow { color:#087f75; font-size:.73rem; letter-spacing:.15em; text-transform:uppercase; font-weight:700; }
.luma-hero { padding:1.8rem 2rem; border:1px solid #dbe7e2; border-radius:22px; background:linear-gradient(120deg,#eaf4ef,#fff 80%); margin-bottom:1.5rem; }
.luma-hero h1 { color:#172e38; font-size:clamp(1.8rem,4vw,2.7rem); line-height:1.18; letter-spacing:-.045em; padding:.55rem 0; }
.luma-hero p { color:#4f656b; max-width:580px; margin:0; line-height:1.65; }
.luma-ready { color:#22675b; background:#edf7f1; border:1px solid #d5eade; border-radius:12px; padding:.65rem 1rem; font-size:.9rem; margin:1.1rem 0; }
.luma-empty { padding:1.5rem 0 .7rem; }
.luma-empty h3 { color:#172e38; font-size:1.25rem; margin-bottom:.4rem; }
.luma-empty p { color:#536970; }
.luma-prompt { background:#fff; border:1px solid #dce5e1; border-radius:14px; padding:1rem; height:100%; color:#334f58; font-size:.94rem; }
.luma-prompt small { display:block; color:#087f75; font-weight:650; margin-bottom:.5rem; }
[data-testid="stChatMessage"] { background:#fff; border:1px solid #e0e8e4; border-radius:18px; padding:1rem; margin:.15rem 0; }
[data-testid="stChatMessage"] p { line-height:1.65; }

[data-testid="stExpander"] { background:#fff; border-radius:12px; }
.stButton button, .stLinkButton a { border-radius:10px; }
button[data-baseweb="tab"] { font-weight:600; }
@media (max-width:640px) { .luma-hero { padding:1.3rem; } }
@media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto!important; } }

/* Neutral navigation; teal indicates selection, not an error state. */
[data-testid="stRadio"] [role="radiogroup"] { gap:.6rem; flex-wrap:wrap; }
[data-testid="stRadio"] label[data-baseweb="radio"] { padding:.55rem .9rem; border:1px solid #d7e3de; border-radius:10px; background:#fff; margin:0; }
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background:#e1f1eb; border-color:#087f75; }
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color:#08695f!important; font-weight:650; }
[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { background:#087f75!important; border-color:#087f75!important; }
[data-testid="stChatMessageAvatarUser"] { background:#e0eee9!important; color:#254f48!important; }
[data-testid="stChatMessageAvatarAssistant"] { background:#087f75!important; color:#fff!important; }

a { color:#087f75; }
.luma-hero { padding:1.1rem 1.6rem; margin-bottom:1rem; }
.luma-hero h1 { font-size:clamp(1.7rem,3vw,2.2rem); }


/* Each exchange keeps its question immediately above its answer. */
[class*="st-key-luma_exchange_"] [data-testid="stVerticalBlock"] { gap:.35rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background:#e5f1ed; border-color:#c6ddd3; padding:.75rem 1rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p {
    color:#173e35; font-weight:600;
}
.luma-order { color:#536970; font-size:.82rem; margin:.4rem 0; }

/* Own the outline on the outer widget; suppress nested default red borders. */
[data-testid="stChatInput"] {
    border:2px solid #a5c9bd!important;
    border-radius:16px!important;
    background:#fff!important;
    box-sizing:border-box!important;
    padding:2px!important;
    overflow:hidden;
    box-shadow:none!important;
}
[data-testid="stChatInput"] div,
[data-testid="stChatInput"] textarea {
    border-color:transparent!important;
    box-shadow:none!important;
    outline:none!important;
}
[data-testid="stChatInput"] > div {
    border-radius:12px!important;
    background:#fff!important;
}
[data-testid="stChatInput"] textarea {
    color:#172e38!important;
    background:#fff!important;
    caret-color:#087f75!important;
}
[data-testid="stChatInput"]:hover { border-color:#519b87!important; }
[data-testid="stChatInput"]:focus-within {
    border-color:#087f75!important;
    outline:3px solid #cce8df!important;
    outline-offset:2px;
}
[data-testid="stChatInput"] button:focus-visible {
    outline:2px solid #087f75!important;
    outline-offset:-2px;
}

</style>
''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="luma-brand"><span>✳</span>Luma</div>', unsafe_allow_html=True)
    st.caption('A little clarity. A lot of learning.')
    st.divider()
    st.header('Your learning space')
    collection = st.selectbox('Document collection', ['ai'], format_func=lambda c: 'AI learning — public')
    style = st.selectbox('Explanation style', ['Beginner-friendly', 'Technical'])
    st.caption('Choose a simple introduction or a more technical explanation.')
    st.divider()
    if st.button('Clear conversation', use_container_width=True):
        st.session_state.messages = []
        st.session_state.previous_question = ''
        st.rerun()
    st.caption('Start a fresh conversation when switching to a new topic.')

if st.session_state.get('collection') != collection:
    st.session_state.collection = collection
    st.session_state.messages = []
    st.session_state.previous_question = ''
st.session_state.setdefault('messages', [])
st.session_state.setdefault('previous_question', '')

st.markdown('''<section class="luma-hero">
<div class="luma-eyebrow">Your AI learning companion</div>
<h1>Learn with clarity.</h1>
<p>Explore your learning materials, untangle a tricky concept, and follow the sources behind each explanation.</p>
</section>''', unsafe_allow_html=True)
section = st.radio('Navigation', ['Conversation', 'Learning library', 'Why these tools?'], horizontal=True, label_visibility='collapsed', key='luma_navigation')

if section == 'Why these tools?':
    st.subheader('Behind your learning experience')
    st.caption('For anyone curious about how Luma is built.')
    st.table([
        {'Tool':'Streamlit', 'Purpose':'The learning interface and chat controls.'},
        {'Tool':'LangChain', 'Purpose':'Connects document processing, models, and document search.'},
        {'Tool':'LangGraph', 'Purpose':'Organizes question routing, retrieval, and response steps.'},
        {'Tool':'Fireworks', 'Purpose':'Creates document embeddings and generates explanations.'},
        {'Tool':'Pinecone', 'Purpose':'Searches indexed document passages by semantic similarity.'},
        {'Tool':'LangSmith', 'Purpose':'Optional tracing for development and evaluation.'},
    ])

if section == 'Learning library':
    st.subheader('Your learning materials')
    st.caption('Browse the documents available to Luma and visit their original sources.')
    try:
        docs = load_documents(collection)
        if not docs:
            st.info('No learning materials are available yet.')
        for d in docs:
            page = d.metadata.get('page')
            title = d.metadata.get('title', 'Learning document')
            label = title + (f' · page {page}' if page else '')
            with st.expander(label):
                if d.metadata.get('license'):
                    st.caption(d.metadata['license'])
                st.text(d.page_content)
                if d.metadata.get('url'):
                    st.link_button('View original source', d.metadata['url'])
    except Exception:
        st.warning('Your learning library could not be loaded. Please try again later.')

def render_message(message):
    with st.chat_message(message['role'], avatar='✳' if message['role']=='assistant' else '👤'):
        st.markdown(message['content'])
        render_sources(message.get('sources', []))

def render_sources(sources):
    if sources:
        st.caption('Explore the source passages')
    for source in sources:
        page = source.get('page')
        label = f'[{source["id"]}] {source.get("title", "Source")}' + (f' · page {page}' if page else '')
        with st.expander(label):
            st.text(source['text'])
            if source.get('url'):
                st.link_button('View original source', source['url'])

def conversation_exchanges(messages):
    """Group chronological messages, then reverse exchanges rather than Q/A order."""
    exchanges = []
    for message in messages:
        if message['role'] == 'user' or not exchanges:
            exchanges.append([])
        exchanges[-1].append(message)
    return list(reversed(exchanges))

if section == 'Conversation':
    ready = manifest_path(collection).exists()
    if ready:
        st.markdown('<div class="luma-ready">● &nbsp; Your learning documents are ready.</div>', unsafe_allow_html=True)
    else:
        st.info('Your learning documents need to be prepared before you can ask questions.')

    # An inline composer keeps the newest exchange at the top, rather than
    # invoking Streamlit's bottom-pinned chat behavior.
    with st.container():
        question = st.chat_input('What would you like to learn?', disabled=not ready, max_chars=2000, key='luma_question')

    history = list(st.session_state.messages)
    if question or history:
        st.markdown('<div class="luma-order">Newest question first · Earlier conversations below</div>', unsafe_allow_html=True)

    # This container is placed BEFORE history, including while the request runs.
    with st.container(key='luma_exchange_latest'):
        if question:
            user_message = {'role':'user', 'content':question}
            st.session_state.messages.append(user_message)
            render_message(user_message)
            with st.chat_message('assistant', avatar='✳'):
                try:
                    reply = feedback_reply(question)
                    if reply:
                        result = {'answer':reply, 'sources':[], 'trace_steps':['handle_feedback_or_greeting']}
                    else:
                        with st.spinner('Luma is preparing your answer…'):
                            graph = create_runtime(collection)
                            result = ask(graph, question, collection, st.session_state.previous_question, style)
                        st.session_state.previous_question = question
                    answer_message = {'role':'assistant', 'content':result['answer'], 'sources':result.get('sources', [])}
                except Exception:
                    answer_message = {'role':'assistant', 'content':'I couldn’t complete that request. Please try again. If it continues, ask the app owner to check the service connection.'}
                st.session_state.messages.append(answer_message)
                st.markdown(answer_message['content'])
                render_sources(answer_message.get('sources', []))

    for index, exchange in enumerate(conversation_exchanges(history)):
        with st.container(key=f'luma_exchange_history_{index}'):
            for message in exchange:
                render_message(message)

    if not history and not question:
        st.markdown('<div class="luma-empty"><h3>What would you like to understand?</h3><p>Ask a question in your own words. Here are a few places to start.</p></div>', unsafe_allow_html=True)
        suggestions = [
            ('Understand a concept', 'How do large language models work?'),
            ('Connect the ideas', 'How does RAG use a vector database?'),
            ('Build your skills', 'What makes a good prompt?'),
        ]
        for column, (label, example) in zip(st.columns(3), suggestions):
            with column:
                st.markdown(f'<div class="luma-prompt"><small>{html.escape(label)}</small>{html.escape(example)}</div>', unsafe_allow_html=True)
        st.caption('Use these examples as inspiration, or type your own question above.')
