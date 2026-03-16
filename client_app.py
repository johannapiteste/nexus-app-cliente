import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, timezone, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Nexus VIP", page_icon="🏆", layout="centered")

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
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        .stApp {background-color: #09090b; color: #f8fafc;}
        div[data-testid="column"]:nth-of-type(2) {
            background-color: #18181b; padding: 30px; border-radius: 12px;
            border: 1px solid #27272a; margin-top: 10vh;
        }
        div.stButton > button[kind="primary"] {
            background-color: #3b82f6; width: 100%; border:none; 
            padding: 10px; border-radius: 8px; font-weight: bold; margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🏆 Nexus VIP</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #a1a1aa;'>Acesso Exclusivo</p>", unsafe_allow_html=True)
        
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
                    else: st.error("Credenciais inválidas.")
                except Exception as e: st.error("Erro na base de dados.")
            else: st.warning("Preencha todos os campos.")
    st.stop()

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
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM bilhetes_vistos WHERE username = %s", (st.session_state.username,))
    vistos_db = set([r[0] for r in cursor.fetchall()])
    cursor.close()
    conn.close()
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

novos_bilhetes = [b for b in bilhetes_abertos_geral if b[0] not in vistos_db]
bilhetes_em_aberto = [b for b in bilhetes_abertos_geral if b[0] in vistos_db]

if 'notificado_hoje' not in st.session_state:
    st.session_state.notificado_hoje = True
    if novos_bilhetes: st.toast(f"✨ Tem {len(novos_bilhetes)} novo(s) bilhete(s) à sua espera!", icon="🎯")
    teve_green_recente = False
    for t_id, group in df_all.groupby('ticket_id'):
        statuses = group['status_resultado'].str.upper().tolist()
        if not any('PENDENTE' in s for s in statuses) and not any('RED' in s for s in statuses) and len(statuses) > 0:
            ultima_atualizacao = pd.to_datetime(group['timestamp'].iloc[0])
            if (get_brt_time().replace(tzinfo=None) - ultima_atualizacao).days <= 1:
                teve_green_recente = True
    if teve_green_recente:
        st.toast("🏆 Um dos seus bilhetes bateu GREEN nas últimas 24h!", icon="✅")
        st.balloons()

with tab1:
    st.info("ℹ️ Novos bilhetes todos os dias às 22:00 Horas")
    if not novos_bilhetes:
        st.success("Não existem bilhetes novos no momento. Verifique a aba 'Aberto'.")
    else:
        if st.button("✅ Marcar todos como Vistos (Mover para Aberto)", type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            for t_id, _ in novos_bilhetes:
                cursor.execute("INSERT INTO bilhetes_vistos (username, ticket_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (st.session_state.username, t_id))
            conn.commit()
            cursor.close()
            conn.close()
            st.rerun()
            
        for t_id, group in novos_bilhetes:
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #8b5cf6;"><h4>✨ {t_id} (NOVO)</h4>', unsafe_allow_html=True)
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

with tab3:
    st.markdown("### 🌟 Hall da Fama")
    bilhetes_vencedores = []
    for t_id, group in df_all.groupby('ticket_id'):
        statuses = group['status_resultado'].str.upper().tolist()
        if not any('PENDENTE' in s for s in statuses) and not any('RED' in s for s in statuses) and len(statuses) > 0:
            bilhetes_vencedores.append((t_id, group))
            
    if not bilhetes_vencedores: st.info("Aguardando os primeiros Greens 100% da rodada atual.")
    else:
        for t_id, group in bilhetes_vencedores:
            st.markdown(f'<div class="ticket-card" style="border-left: 4px solid #10b981;"><h4>🏆 {t_id}</h4>', unsafe_allow_html=True)
            for _, j in group.iterrows():
                placar = j.get('placar_real', '-')
                hora_str = f"{j.get('data_jogo', '--/--')} {j.get('hora_jogo', '--:--')} BRT"
                st.markdown(f"""
                    <div class="game-card">
                        <div style="font-size:0.75rem; color:#a1a1aa; margin-bottom:4px;">⏰ {hora_str} • {j.get('liga', '')}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">{j['confronto']}</span>
                            <span class="status-badge green">{placar}</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem; color:#10b981;">✅ <span style="font-weight:800;">{str(j.get('vencedor_previsto', '')).upper()}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown("### ⏰ Próximos Jogos")
    df_pendentes = df_all[df_all['status_resultado'] == 'PENDENTE'].copy()
    
    if df_pendentes.empty:
        st.success("Não há jogos pendentes mapeados.")
    else:
        jogos_lista = df_pendentes.to_dict('records')
        agora = get_brt_time().replace(tzinfo=None)
        ano_atual = agora.year
        
        jogos_futuros = []
        for j in jogos_lista:
            try:
                # Usa a hora e dia reais em relação ao ano atual para verificar se o jogo já começou ou ficou para trás
                dt_str = f"{j.get('data_jogo', '01/01')}/{ano_atual} {j.get('hora_jogo', '00:00')}"
                sort_t = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                j['sort_time'] = sort_t
                
                # Se o jogo ainda NÃO aconteceu (hora futura), entra na lista
                if sort_t > agora:
                    jogos_futuros.append(j)
            except:
                pass
                
        jogos_futuros = sorted(jogos_futuros, key=lambda x: x['sort_time'])
        
        if not jogos_futuros:
            st.success("Todos os jogos dos bilhetes atuais já começaram ou estão pendentes de resultado.")
        else:
            for j in jogos_futuros:
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
                    <div class="metric-box" style="flex:1; background:#18181b; padding:15px; border-radius:10px; border:1px solid #27272a; text-align:center;">
                        <div style="color:#a1a1aa; font-size:0.85rem;">Bilhetes no Mês</div>
                        <div style="font-size:1.5rem; font-weight:800;">{len(df_mes_atual)}</div>
                    </div>
                    <div class="metric-box" style="flex:1; background:#18181b; padding:15px; border-radius:10px; border:1px solid #27272a; text-align:center;">
                        <div style="color:#a1a1aa; font-size:0.85rem;">Lucro Líquido</div>
                        <div style="font-size:1.5rem; font-weight:800; color:{cor_lucro};">R$ {l_liq:.2f}</div>
                    </div>
                    <div class="metric-box" style="flex:1; background:#18181b; padding:15px; border-radius:10px; border:1px solid #27272a; text-align:center;">
                        <div style="color:#a1a1aa; font-size:0.85rem;">ROI (%)</div>
                        <div style="font-size:1.5rem; font-weight:800; color:{cor_lucro};">{roi:.1f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 📈 Evolução da Banca Mensal")
            df_mensal = df_banca.groupby('Mês')['Lucro'].sum().reset_index()
            st.bar_chart(df_mensal.set_index('Mês')['Lucro'])
