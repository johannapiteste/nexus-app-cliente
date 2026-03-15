import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, timezone, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Nexus VIP", page_icon="🏆", layout="centered")

# --- INJEÇÃO DE MANIFESTO PARA PWA (Opcional, tentar forçar nome) ---
st.markdown("""
    <script>
        document.title = "Nexus VIP";
        var link = document.querySelector("link[rel~='icon']");
        if (!link) {
            link = document.createElement('link');
            link.rel = 'icon';
            document.head.appendChild(link);
        }
        link.href = 'https://em-content.zobj.net/source/apple/354/trophy_1f3c6.png';
    </script>
""", unsafe_allow_html=True)

def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def get_brt_time():
    return datetime.now(timezone(timedelta(hours=-3)))

# --- SISTEMA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("""
        <style>
        .stApp {background-color: #09090b; color: #f8fafc;}
        .login-box {background: #18181b; padding: 30px; border-radius: 12px; border: 1px solid #27272a; text-align: center; margin-top: 50px;}
        div.stButton > button[kind="primary"] {background-color: #3b82f6; width: 100%; border:none; padding: 10px; border-radius: 8px;}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.title("🏆 Nexus VIP")
        st.write("Acesso Exclusivo")
        
        user_input = st.text_input("Utilizador").lower()
        pass_input = st.text_input("Password", type="password")
        
        if st.button("Entrar", type="primary"):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM usuarios WHERE username = %s", (user_input,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result and result[0] == pass_input:
                    st.session_state.logged_in = True
                    st.session_state.username = user_input
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
            except Exception as e:
                st.error("Erro na base de dados.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Pára o script aqui se não estiver logado

# --- ESTILIZAÇÃO DO APP LOGADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp {background-color: #09090b; color: #f8fafc; font-family: 'Inter', sans-serif;}
    .ticket-card {background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 15px; margin-bottom: 15px;}
    .game-card {background: #27272a; border-radius: 8px; padding: 10px; margin-top: 8px;}
    .status-badge {padding: 2px 8px; border-radius: 4px; font-weight: 800; font-size: 0.8rem;}
    .green {background: #064e3b; color: #34d399;}
    div.stButton > button[kind="primary"] {background-color: #8b5cf6; color: #ffffff; border-radius: 8px; font-weight: 700; width: 100%; border: none;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

col_title, col_logout = st.columns([0.8, 0.2])
col_title.title("🏆 Nexus VIP")
if col_logout.button("Sair"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown(f"<p style='color: #a1a1aa; margin-top:-15px;'>Bem-vindo, <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌟 Novos", "🎫 Em Aberto", "🏆 Vencedores", "⏰ Próximos", "🏦 P&L"])

try:
    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM previsoes WHERE ticket_id IS NOT NULL AND ticket_id != '' AND ticket_id NOT LIKE 'OCULTO_%'", conn)
    
    # Busca bilhetes já vistos pelo usuário atual
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM bilhetes_vistos WHERE username = %s", (st.session_state.username,))
    vistos_db = set([r[0] for r in cursor.fetchall()])
    
except Exception as e:
    st.error("Erro ao ligar à base de dados.")
    st.stop()

if df_all.empty:
    st.info("Nenhum dado disponível no momento.")
    st.stop()

bilhetes_abertos_geral = []
for t_id, group in df_all.groupby('ticket_id'):
    statuses = group['status_resultado'].str.upper().tolist()
    if any('PENDENTE' in s for s in statuses) and not any('RED' in s for s in statuses):
        bilhetes_abertos_geral.append((t_id, group))

# Lógica Perene com Banco de Dados
novos_bilhetes = [b for b in bilhetes_abertos_geral if b[0] not in vistos_db]
bilhetes_em_aberto = [b for b in bilhetes_abertos_geral if b[0] in vistos_db]

with tab1:
    st.info("ℹ️ Novos bilhetes todos os dias às 22:00 Horas")
    if not novos_bilhetes:
        st.success("Não existem bilhetes novos no momento. Verifique a aba 'Em Aberto'.")
    else:
        if st.button("✅ Marcar todos como Vistos (Mover para Em Aberto)", type="primary"):
            for t_id, _ in novos_bilhetes:
                cursor.execute("INSERT INTO bilhetes_vistos (username, ticket_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (st.session_state.username, t_id))
            conn.commit()
            st.rerun()
            
        for t_id, group in novos_bilhetes:
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #8b5cf6;"><h4>✨ {t_id} (NOVO)</h4>', unsafe_allow_html=True)
            for _, j in group.iterrows():
                hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
                st.markdown(f"""
                    <div class="game-card">
                        <div style="font-size:0.75rem; color:#a1a1aa;">⏰ {hora_str} • {j.get('liga', '')}</div>
                        <div style="font-weight:600;">{j['confronto']}</div>
                        <div style="margin-top:6px; font-size:0.85rem;">🎯 Pick: <span style="font-weight:800;">{str(j.get('vencedor_previsto', '')).upper()}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("### 🎫 Bilhetes Ativos (Acompanhamento)")
    if not bilhetes_em_aberto:
        st.info("Os bilhetes que marcar como lidos aparecerão aqui.")
    else:
        for t_id, group in bilhetes_em_aberto:
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #3b82f6;"><h4>⏳ {t_id}</h4>', unsafe_allow_html=True)
            for _, j in group.iterrows():
                status = j.get('status_resultado', 'PENDENTE').replace('ARQUIVADO ', '')
                hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
                st.markdown(f"""
                    <div class="game-card">
                        <div style="font-size:0.75rem; color:#a1a1aa;">⏰ {hora_str}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">{j['confronto']}</span>
                            <span style="color:#fbbf24; font-weight:800; font-size:0.85rem;">{status}</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem;">🎯 Pick: <span style="font-weight:800;">{str(j.get('vencedor_previsto', '')).upper()}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tab3: st.write("Oculto para resumir (Mesma lógica de Vencedores)")
with tab4: st.write("Oculto para resumir (Mesma lógica Próximos)")
with tab5: st.write("Oculto para resumir (Mesma lógica P&L)")

# Fecha BD no final
try:
    cursor.close()
    conn.close()
except: pass
