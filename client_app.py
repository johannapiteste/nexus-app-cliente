import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, timezone, timedelta

# --- CONFIGURAÇÃO DA PÁGINA (Altera o nome no telemóvel) ---
st.set_page_config(page_title="Nexus VIP", page_icon="🏆", layout="centered")

# --- INJEÇÃO DE MANIFESTO PARA PWA (Opcional, tentar forçar nome e ícone) ---
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
        div.stButton > button[kind="primary"] {background-color: #3b82f6; width: 100%; border:none; padding: 10px; border-radius: 8px; font-weight: bold;}
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
            if user_input and pass_input:
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
                        st.error("Credenciais inválidas. Verifique os dados.")
                except Exception as e:
                    st.error("Erro na base de dados. Verifique se os Secrets estão configurados.")
            else:
                st.warning("Preencha todos os campos para entrar.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Bloqueia a execução do resto do código se não estiver logado

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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌟 Novos", "🎫 Aberto", "🏆 Vencedores", "⏰ Próximos", "🏦 P&L"])

try:
    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM previsoes WHERE ticket_id IS NOT NULL AND ticket_id != '' AND ticket_id NOT LIKE 'OCULTO_%'", conn)
    
    # Busca bilhetes já vistos pelo utilizador atual diretamente da Base de Dados
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM bilhetes_vistos WHERE username = %s", (st.session_state.username,))
    vistos_db = set([r[0] for r in cursor.fetchall()])
    
except Exception as e:
    st.error("Erro ao ligar à base de dados.")
    st.stop()

if df_all.empty:
    st.info("Nenhum dado disponível no momento.")
    try:
        cursor.close()
        conn.close()
    except: pass
    st.stop()

bilhetes_abertos_geral = []
for t_id, group in df_all.groupby('ticket_id'):
    statuses = group['status_resultado'].str.upper().tolist()
    # Puxa bilhetes que não foram concluídos (não têm Red, e ainda têm Pendentes)
    if any('PENDENTE' in s for s in statuses) and not any('RED' in s for s in statuses):
        bilhetes_abertos_geral.append((t_id, group))

# Cruza os bilhetes com os que o utilizador já marcou como "Vistos"
novos_bilhetes = [b for b in bilhetes_abertos_geral if b[0] not in vistos_db]
bilhetes_em_aberto = [b for b in bilhetes_abertos_geral if b[0] in vistos_db]

# --- ABA 1: NOVOS BILHETES ---
with tab1:
    st.info("ℹ️ Novos bilhetes todos os dias às 22:00 Horas")
    if not novos_bilhetes:
        st.success("Não existem bilhetes novos no momento. Verifique a aba 'Aberto'.")
    else:
        if st.button("✅ Marcar todos como Vistos (Mover para Aberto)", type="primary"):
            for t_id, _ in novos_bilhetes:
                # Insere os bilhetes na base de dados para que fiquem permanentemente salvos como vistos para este cliente
                cursor.execute("INSERT INTO bilhetes_vistos (username, ticket_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (st.session_state.username, t_id))
            conn.commit()
            st.rerun()
            
        for t_id, group in novos_bilhetes:
            odd_multipla = 1.0
            for _, j in group.iterrows():
                casa_nome = str(j.get('confronto', '')).split(' vs ')[0].strip().lower()
                pick = str(j.get('vencedor_previsto', '')).strip().lower()
                if 'empate' in pick: odd_jogo = float(j.get('odd_empate', 1.0))
                elif casa_nome in pick: odd_jogo = float(j.get('odd_casa', 1.0))
                else: odd_jogo = float(j.get('odd_fora', 1.0))
                if odd_jogo <= 1.0: odd_jogo = max(float(j.get('odd_casa', 1.0)), float(j.get('odd_fora', 1.0)))
                odd_multipla *= max(odd_jogo, 1.0)
                
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #8b5cf6;"><h4>✨ {t_id} (NOVO)<br><span style="color:#8b5cf6; font-size:0.9rem;">🔥 Odd Múltipla: {odd_multipla:.2f}</span></h4>', unsafe_allow_html=True)
            for _, j in group.iterrows():
                hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
                st.markdown(f"""
                    <div class="game-card">
                        <div style="font-size:0.75rem; color:#a1a1aa; margin-bottom:4px;">⏰ {hora_str} • {j.get('liga', '')}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">{j['confronto']}</span>
                            <span style="color:#fbbf24; font-weight:800; font-size:0.85rem;">⏳ PENDENTE</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem;">🎯 Pick: <span style="font-weight:800;">{str(j.get('vencedor_previsto', '')).upper()}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: BILHETES EM ABERTO ---
with tab2:
    st.markdown("### 🎫 Bilhetes Ativos (Acompanhamento)")
    if not bilhetes_em_aberto:
        st.info("Os bilhetes que marcar como lidos aparecerão aqui.")
    else:
        for t_id, group in bilhetes_em_aberto:
            odd_multipla = 1.0
            for _, j in group.iterrows():
                casa_nome = str(j.get('confronto', '')).split(' vs ')[0].strip().lower()
                pick = str(j.get('vencedor_previsto', '')).strip().lower()
                if 'empate' in pick: odd_jogo = float(j.get('odd_empate', 1.0))
                elif casa_nome in pick: odd_jogo = float(j.get('odd_casa', 1.0))
                else: odd_jogo = float(j.get('odd_fora', 1.0))
                if odd_jogo <= 1.0: odd_jogo = max(float(j.get('odd_casa', 1.0)), float(j.get('odd_fora', 1.0)))
                odd_multipla *= max(odd_jogo, 1.0)
                
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #3b82f6;"><h4>⏳ {t_id}<br><span style="color:#3b82f6; font-size:0.9rem;">🔥 Odd Múltipla: {odd_multipla:.2f}</span></h4>', unsafe_allow_html=True)
            for _, j in group.iterrows():
                status = j.get('status_resultado', 'PENDENTE').replace('ARQUIVADO ', '')
                hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
                cor_status = "#34d399" if "GREEN" in status else "#fbbf24"
                icon = "✅" if "GREEN" in status else "⏳"
                
                st.markdown(f"""
                    <div class="game-card">
                        <div style="font-size:0.75rem; color:#a1a1aa; margin-bottom:4px;">⏰ {hora_str} • {j.get('liga', '')}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">{j['confronto']}</span>
                            <span style="color:{cor_status}; font-weight:800; font-size:0.85rem;">{icon} {status}</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem;">🎯 Pick: <span style="font-weight:800;">{str(j.get('vencedor_previsto', '')).upper()}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 3: VENCEDORES (HALL DA FAMA) ---
with tab3:
    st.markdown("### 🌟 Hall da Fama")
    bilhetes_vencedores = []
    for t_id, group in df_all.groupby('ticket_id'):
        statuses = group['status_resultado'].str.upper().tolist()
        if not any('PENDENTE' in s for s in statuses) and not any('RED' in s for s in statuses) and len(statuses) > 0:
            bilhetes_vencedores.append((t_id, group))
            
    if not bilhetes_vencedores:
        st.info("Aguardando os primeiros Greens 100% da rodada atual.")
    else:
        for t_id, group in bilhetes_vencedores:
            odd_multipla = 1.0
            for _, j in group.iterrows():
                casa_nome = str(j.get('confronto', '')).split(' vs ')[0].strip().lower()
                pick = str(j.get('vencedor_previsto', '')).strip().lower()
                if 'empate' in pick: odd_jogo = float(j.get('odd_empate', 1.0))
                elif casa_nome in pick: odd_jogo = float(j.get('odd_casa', 1.0))
                else: odd_jogo = float(j.get('odd_fora', 1.0))
                if odd_jogo <= 1.0: odd_jogo = max(float(j.get('odd_casa', 1.0)), float(j.get('odd_fora', 1.0)))
                odd_multipla *= max(odd_jogo, 1.0)
                
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #10b981;"><h4>🏆 {t_id} <br><span style="color:#10b981; font-size:0.9rem;">🔥 Odd Múltipla: {odd_multipla:.2f}</span></h4>', unsafe_allow_html=True)
            for _, j in group.iterrows():
                pick = str(j.get('vencedor_previsto', '')).upper()
                placar = j.get('placar_real', '-')
                hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
                st.markdown(f"""
                    <div class="game-card">
                        <div style="font-size:0.75rem; color:#a1a1aa; margin-bottom:4px;">⏰ {hora_str} • {j.get('liga', '')}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">{j['confronto']}</span>
                            <span class="status-badge green">{placar}</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem; color:#10b981;">✅ <span style="font-weight:800;">{pick}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 4: PRÓXIMOS JOGOS ---
with tab4:
    st.markdown("### ⏰ Próximos Jogos")
    df_pendentes = df_all[df_all['status_resultado'] == 'PENDENTE'].copy()
    
    if df_pendentes.empty:
        st.success("Não há jogos mapeados prestes a começar.")
    else:
        jogos_lista = df_pendentes.to_dict('records')
        for j in jogos_lista:
            try:
                j['sort_time'] = datetime.strptime(f"{j.get('data_jogo', '01/01')} {j.get('hora_jogo', '00:00')}", "%d/%m %H:%M")
            except:
                j['sort_time'] = datetime.now()
                
        jogos_lista = sorted(jogos_lista, key=lambda x: x['sort_time'])
        
        for j in jogos_lista:
            hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
            ticket = j.get('ticket_id', 'Bilhete Desconhecido')
            st.markdown(f"""
                <div class="ticket-card" style="border-left: 4px solid #f59e0b; padding:12px;">
                    <div style="font-size:0.75rem; color:#fbbf24; font-weight:800; margin-bottom:4px;">⏰ {hora_str} • Pertence ao {ticket}</div>
                    <div style="font-weight:800; font-size:1.05rem; margin-bottom:4px;">⚽ {j['confronto']}</div>
                    <div style="font-size:0.85rem; color:#a1a1aa;">🏆 {j.get('liga', '')}</div>
                    <div style="margin-top:8px; border-top:1px solid #27272a; padding-top:8px;">
                        <span style="font-size:0.85rem; color:#e4e4e7;">Entrada da IA: </span>
                        <span style="color:#f8fafc; font-weight:800;">{str(j.get('vencedor_previsto', '')).upper()}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- ABA 5: LUCRO E PERDA (P&L) ---
with tab5:
    st.markdown("### 🏦 Relatório Financeiro")
    df_tickets = df_all[~df_all['status_resultado'].str.contains('ARQUIVADO', na=False)]
    
    if df_tickets.empty:
        st.info("O relatório será gerado assim que houver bilhetes finalizados (Green/Red).")
    else:
        dados_banca = []
        for t_id, group in df_tickets.groupby('ticket_id'):
            statuses = group['status_resultado'].str.upper().tolist()
            is_pendente = any('PENDENTE' in s for s in statuses)
            is_red = any('RED' in s for s in statuses)
            is_green = all('GREEN' in s for s in statuses)
            
            if is_pendente or (not is_red and not is_green): continue 
            
            odd_m = 1.0
            for _, j in group.iterrows():
                casa_nome = str(j.get('confronto','')).split(' vs ')[0].strip().lower()
                pick = str(j.get('vencedor_previsto','')).strip().lower()
                if 'empate' in pick: odd_j = float(j.get('odd_empate', 1.0))
                elif casa_nome in pick: odd_j = float(j.get('odd_casa', 1.0))
                else: odd_j = float(j.get('odd_fora', 1.0))
                if odd_j <= 1.0: odd_j = max(float(j.get('odd_casa', 1.0)), float(j.get('odd_fora', 1.0)))
                odd_m *= max(odd_j, 1.0)
            
            dt_obj = pd.to_datetime(group['timestamp'].iloc[0])
            mes_ano = dt_obj.strftime("%m/%Y")
            
            investimento = 1.00
            retorno = (investimento * odd_m) if is_green else 0.00
            lucro = retorno - investimento
            
            dados_banca.append({"Mês": mes_ano, "Investimento": investimento, "Lucro": lucro})

        if not dados_banca:
            st.info("Todos os bilhetes atuais estão Pendentes.")
        else:
            df_banca = pd.DataFrame(dados_banca)
            mes_atual = get_brt_time().strftime("%m/%Y")
            df_mes_atual = df_banca[df_banca['Mês'] == mes_atual]
            
            t_inv = df_mes_atual['Investimento'].sum()
            l_liq = df_mes_atual['Lucro'].sum()
            roi = (l_liq / t_inv * 100) if t_inv > 0 else 0
            
            cor_lucro = "#34d399" if l_liq >= 0 else "#ef4444"
            
            st.markdown(f"""
                <div style="display:flex; gap:10px; margin-bottom:20px;">
                    <div class="metric-box" style="flex:1;">
                        <div style="color:#a1a1aa; font-size:0.85rem;">Bilhetes no Mês</div>
                        <div style="font-size:1.5rem; font-weight:800;">{len(df_mes_atual)}</div>
                    </div>
                    <div class="metric-box" style="flex:1;">
                        <div style="color:#a1a1aa; font-size:0.85rem;">Lucro Líquido ({mes_atual})</div>
                        <div style="font-size:1.5rem; font-weight:800; color:{cor_lucro};">R$ {l_liq:.2f}</div>
                    </div>
                    <div class="metric-box" style="flex:1;">
                        <div style="color:#a1a1aa; font-size:0.85rem;">ROI (%)</div>
                        <div style="font-size:1.5rem; font-weight:800; color:{cor_lucro};">{roi:.1f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 📈 Evolução da Banca Mensal")
            df_mensal = df_banca.groupby('Mês')['Lucro'].sum().reset_index()
            st.bar_chart(df_mensal.set_index('Mês')['Lucro'])

# Fecha a base de dados de forma segura no final do script
try:
    cursor.close()
    conn.close()
except: pass
