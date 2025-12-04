import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import tempfile
import os
import gspread
from google.oauth2.service_account import Credentials
import io # Importante para o Excel

# --- SEGURANÇA PLOTLY ---
try:
    import plotly.express as px
    PLOTLY_ATIVO = True
except ImportError:
    PLOTLY_ATIVO = False

# ==============================================================================
# 1. CONFIGURAÇÃO GERAL
# ==============================================================================
st.set_page_config(page_title="Gerador de Propostas", page_icon="💼", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F4F6F9; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #E6E9EF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 28px; color: #2C3E50; font-weight: 800; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 8px; height: 45px; }
    .stDataFrame { border: 1px solid #ddd; border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM GOOGLE SHEETS
# ==============================================================================
SHEET_TABS = {
    "Materiais": "db_materiais",
    "MaoDeObra": "db_mdo",
    "Kits": "db_kits",
    "Config_Acionamentos": "db_conf_acion",
    "Config_Vasos": "db_conf_vasos",
    "Config_Hidraulica": "db_conf_hidra"
}

DEFAULT_DATA = {
    "Materiais": {'ID_Material': ['CLP-PADRAO'], 'Descricao': ['Material Exemplo'], 'Grupo_Orcamento': ['Geral'], 'Preco_Custo': [100.0]},
    "Kits": {'ID_Kit': [], 'ID_Material': [], 'Quantidade': []},
    "Config_Vasos": pd.DataFrame(),
    "Config_Hidraulica": pd.DataFrame(),
    "Config_Acionamentos": pd.DataFrame()
}

def get_google_connection():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro na conexão com Google: {e}")
        return None

@st.cache_data(ttl=60)
def load_data_from_sheets():
    client = get_google_connection()
    if not client: return {k: pd.DataFrame(v) if isinstance(v, dict) else v for k,v in DEFAULT_DATA.items()}
    
    dataframes = {}
    try:
        sheet = client.open("Sistema_Orcamento_DB")
        for key, tab_name in SHEET_TABS.items():
            try:
                worksheet = sheet.worksheet(tab_name)
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                if 'Preco_Custo' in df.columns: df['Preco_Custo'] = pd.to_numeric(df['Preco_Custo'], errors='coerce').fillna(0)
                if 'Quantidade' in df.columns: df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
                dataframes[key] = df
            except:
                dataframes[key] = pd.DataFrame()
        return dataframes
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return {k: pd.DataFrame(v) if isinstance(v, dict) else v for k,v in DEFAULT_DATA.items()}

def save_data_to_sheets(key, df):
    client = get_google_connection()
    if not client: return
    try:
        sheet = client.open("Sistema_Orcamento_DB")
        tab_name = SHEET_TABS[key]
        worksheet = sheet.worksheet(tab_name)
        worksheet.clear()
        body = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(values=body)
        st.toast(f"✅ {key} salvo na nuvem!", icon="☁️")
        load_data_from_sheets.clear()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

db = load_data_from_sheets()

# ==============================================================================
# 3. LOGIN & ESTRUTURA
# ==============================================================================
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False

def check_login(u, p):
    if u == "admin" and p == "1234":
        st.session_state.admin_logged_in = True; st.rerun()
    else: st.sidebar.error("Senha incorreta")

def logout(): st.session_state.admin_logged_in = False; st.rerun()

with st.sidebar:
    st.title("🛡️ Admin")
    if not st.session_state.admin_logged_in:
        u = st.text_input("User", key="login_u"); p = st.text_input("Pass", type="password", key="login_p")
        if st.button("Entrar", key="btn_login"): check_login(u, p)
    else:
        st.success("Conectado ao Google Sheets ☁️")
        if st.button("Sair"): logout()
        st.divider()
        logo = st.file_uploader("Logo PDF", type=['png', 'jpg'])
        if logo: st.image(logo, width=150)
        with st.expander("Empresa"):
            en = st.text_input("Nome", "Empresa Ltda")
            ee = st.text_input("End", "Rua X")
            et = st.text_input("Tel", "(11) 999")
            em = st.text_input("Email", "contato@")
            es = st.text_input("Site", "www")
        st.divider()
        if st.button("🔄 Recarregar Dados da Nuvem"):
            load_data_from_sheets.clear()
            st.rerun()

    if not st.session_state.admin_logged_in: logo, en, ee, et, em, es = None, "Empresa", "", "", "", ""

# ==============================================================================
# 4. CLASSE PDF & EXCEL
# ==============================================================================
class PropostaPDF(FPDF):
    def __init__(self, emp, cli, logo=None):
        super().__init__(); self.emp = emp; self.cli = cli; self.logo = logo
    def header(self):
        if self.page_no() == 1:
            if self.logo:
                try: self.image(self.logo, 10, 8, 33)
                except: pass
            self.set_font('Arial', 'B', 12); self.cell(0, 5, self.emp['nome'], 0, 1, 'R')
            self.set_font('Arial', '', 9); self.cell(0, 5, self.emp['endereco'], 0, 1, 'R')
            self.cell(0, 5, f"Tel: {self.emp['telefone']} | Email: {self.emp['email']}", 0, 1, 'R')
            self.cell(0, 5, self.emp['site'], 0, 1, 'R'); self.ln(10)
            self.set_font('Arial', 'B', 16); self.set_text_color(0, 51, 102)
            self.cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'C'); self.ln(5); self.set_text_color(0)
        else: self.ln(10)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    def chapter_info(self):
        if self.page_no() == 1:
            self.set_fill_color(240); self.set_font('Arial', 'B', 10); self.cell(0, 8, " DADOS CLIENTE", 1, 1, 'L', 1)
            self.set_font('Arial', '', 10); self.cell(0, 6, f"Cliente: {self.cli['nome']}", 0, 1)
            self.cell(0, 6, f"Proj: {self.cli['projeto']}", 0, 1); self.cell(0, 6, f"Valid: {self.cli['validade']}", 0, 1); self.ln(5)
    def chapter_tab(self, df):
        self.set_fill_color(0, 51, 102); self.set_text_color(255); self.set_font('Arial', 'B', 9)
        self.cell(100, 8, "Item", 1, 0, 'L', 1); self.cell(20, 8, "Qtd", 1, 0, 'C', 1)
        self.cell(35, 8, "Unit", 1, 0, 'R', 1); self.cell(35, 8, "Total", 1, 1, 'R', 1)
        self.set_text_color(0); self.set_font('Arial', '', 9); fill = False
        for _, r in df.iterrows():
            self.set_fill_color(245); self.cell(100, 7, str(r['Descrição'])[:55], 1, 0, 'L', fill)
            self.cell(20, 7, str(r['Qtd']), 1, 0, 'C', fill); self.cell(35, 7, f"{r['Venda Unit']:,.2f}", 1, 0, 'R', fill)
            self.cell(35, 7, f"{r['Total Venda']:,.2f}", 1, 1, 'R', fill); fill = not fill
        self.ln(2); self.set_font('Arial', 'B', 12); self.cell(0, 10, f"TOTAL: R$ {df['Total Venda'].sum():,.2f}", 0, 1, 'R'); self.ln(5)
    def chapter_end(self):
        self.set_font('Arial', 'B', 10); self.set_fill_color(240); self.cell(0, 8, " CONDIÇÕES", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10); self.multi_cell(0, 6, f"Prazo: {self.cli['prazo']}\nPag: {self.cli['pagamento']}")
        self.ln(20); y = self.get_y(); self.line(20, y, 90, y); self.line(120, y, 190, y)
        self.cell(95, 5, self.emp['nome'], 0, 0, 'C'); self.cell(95, 5, "Cliente", 0, 1, 'C')

def convert_df_to_excel(df):
    """Converte o DataFrame para Excel em memória"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Orcamento')
        # Ajuste automático de largura das colunas (Opcional, mas fica bonito)
        worksheet = writer.sheets['Orcamento']
        for i, col in enumerate(df.columns):
            width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, width)
    return output.getvalue()

# ==============================================================================
# 5. CÁLCULO
# ==============================================================================
def calc(n, t, d, m):
    try:
        if db["Materiais"].empty or db["Config_Acionamentos"].empty: return None

        rp = db["Config_Acionamentos"][db["Config_Acionamentos"]['Num_Vasos'] == n].iloc[0]
        rv = db["Config_Vasos"][db["Config_Vasos"]['Descricao_Vaso'] == t].iloc[0]
        dh = db["Config_Hidraulica"]
        fh = (dh['Descricao_Vaso'] == t) & (dh['ID_Diametro_mm'] == d)
        if fh.sum() == 0: return None
        ikh = dh[fh].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        ikp = rp['ID_Kit_Painel_Eletrico']

        it = []
        it.append({'ID': rp['ID_Material_CLP'], 'Qtd': 1, 'Type': 'M'})
        it.append({'ID': rp['ID_Material_Painel'], 'Qtd': 1, 'Type': 'M'})
        it.append({'ID': rp['ID_Material_IHM'], 'Qtd': 1, 'Type': 'M'})
        it.append({'ID': rv['ID_Material_Vaso'], 'Qtd': n, 'Type': 'M'})
        
        dk = db["Kits"]
        for k, f in [(ikp, 1), (ikh, n)]:
            ki = dk[dk['ID_Kit'] == k]
            for _, r in ki.iterrows(): it.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade']*f, 'Type': 'M'})

        it.append({'ID': 'MDO-MONT-ELET', 'Qtd': rp['Horas_MDO_Mont_Elet'], 'Type': 'S'})
        it.append({'ID': 'MDO-PROG-CLP', 'Qtd': rp['Horas_MDO_Prog_CLP'], 'Type': 'S'})
        it.append({'ID': 'MDO-MONT-HIDR', 'Qtd': rv['Horas_MDO_Hidr_p_Vaso']*n, 'Type': 'S'})

        res = []; dm = db["Materiais"]; ds = db["MaoDeObra"]
        for i in it:
            if i['Type'] == 'M':
                d = dm[dm['ID_Material'] == i['ID']]
                if d.empty: continue
                desc, grp, cust = d.iloc[0]['Descricao'], d.iloc[0]['Grupo_Orcamento'], float(d.iloc[0]['Preco_Custo'])
                mrg = m.get(grp, 0)
            else:
                d = ds[ds['ID_MaoDeObra'] == i['ID']]
                if d.empty: continue
                desc, grp, cust = d.iloc[0]['Tipo_Servico'], "Mão de Obra", float(d.iloc[0]['Custo_Hora'])
                mrg = m.get("MDO_Elet" if "ELET" in i['ID'] else "MDO_Prog" if "PROG" in i['ID'] else "MDO_Hidr", 0)

            uv = cust * (1 + mrg/100)
            res.append({'Incluir': True, 'Descrição': desc, 'Grupo': grp, 'Qtd': i['Qtd'], 'Custo Unit': cust, 'Venda Unit': uv, 'Total Venda': uv*i['Qtd'], 'Total Custo': cust*i['Qtd']})
        return pd.DataFrame(res)
    except Exception as e:
        return None

# ==============================================================================
# 6. APP TABS
# ==============================================================================
tabs = st.tabs(["📊 Proposta", "🛠️ Kits", "🗃️ Dados (Google Sheets)"]) if st.session_state.admin_logged_in else st.tabs(["📊 Proposta"])

with tabs[0]:
    st.title("Gerador de Propostas")
    
    if db["Config_Vasos"].empty:
        st.error("⚠️ Conexão estabelecida, mas as tabelas estão vazias. Verifique se você colou os dados CSV na Planilha Google.")
    else:
        c1, c2, c3 = st.columns(3)
        nv = c1.selectbox("Vasos", [1,2,3,4], index=3, key="sel_vasos")
        
        opts_t = db["Config_Vasos"]['Descricao_Vaso'].unique() if not db["Config_Vasos"].empty else []
        tv = c2.selectbox("Tamanho", opts_t, index=3 if len(opts_t)>3 else 0, key="sel_tam")
        
        opts_d = db["Config_Hidraulica"]['ID_Diametro_mm'].unique() if not db["Config_Hidraulica"].empty else []
        dt = c3.selectbox("Diâmetro", opts_d, index=1 if len(opts_d)>1 else 0, key="sel_dia")
        
        st.divider()
        with st.expander("⚙️ Margens (%)", expanded=True):
            cm = st.columns(7)
            m = {
                "CLP": cm[0].number_input("CLP", 0, 500, 50, key="m_clp"), 
                "Itens de Painel": cm[1].number_input("Painel", 0, 500, 50, key="m_pnl"),
                "Hidráulica": cm[2].number_input("Peças Hidr.", 0, 500, 50, key="m_hid_peca"), 
                "Vasos": cm[3].number_input("Vasos", 0, 500, 50, key="m_vaso"),
                "MDO_Elet": cm[4].number_input("MDO Elet.", 0, 500, 50, key="m_mdo_elet"), 
                "MDO_Prog": cm[5].number_input("MDO Prog.", 0, 500, 50, key="m_mdo_prog"),
                "MDO_Hidr": cm[6].number_input("MDO Hidr.", 0, 500, 50, key="m_mdo_hidr")
            }
        
        df = calc(nv, tv, dt, m)
        if df is None: st.warning("Configuração incompleta na planilha. Verifique as abas Config.")
        else:
            st.divider()
            edited = st.data_editor(df, column_config={"Incluir": st.column_config.CheckboxColumn(width="small"), "Custo Unit": st.column_config.NumberColumn(format="R$ %.2f"), "Venda Unit": st.column_config.NumberColumn(format="R$ %.2f"), "Total Venda": st.column_config.NumberColumn(format="R$ %.2f")}, disabled=["Descrição", "Grupo", "Qtd", "Custo Unit", "Venda Unit", "Total Venda"], hide_index=True, use_container_width=True, key="main_edit")
            
            fin = edited[edited['Incluir']].copy()
            vt = fin['Total Venda'].sum(); ct = fin['Total Custo'].sum(); lc = vt - ct; lp = (lc/ct*100) if ct>0 else 0
            
            st.divider()
            c_k, c_g = st.columns([1,1])
            with c_k:
                st.markdown("#### 💹 Resumo Financeiro")
                k1, k2 = st.columns(2); k1.metric("Venda", f"R$ {vt:,.2f}"); k2.metric("Custo", f"R$ {ct:,.2f}")
                k3, k4 = st.columns(2); k3.metric("Lucro", f"R$ {lc:,.2f}"); k4.metric("Margem", f"{lp:.1f}%")
            with c_g:
                st.markdown("#### 🍰 Distribuição do Lucro")
                if PLOTLY_ATIVO and lc > 0:
                    g = fin.groupby("Grupo")[["Total Venda", "Total Custo"]].sum().reset_index(); g["L"] = g["Total Venda"] - g["Total Custo"]
                    fig = px.pie(g, values="L", names="Grupo", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=250); st.plotly_chart(fig, use_container_width=True)

            st.divider()
            with st.expander("📝 Cliente", expanded=False):
                cc1, cc2 = st.columns(2); cn = cc1.text_input("Nome", "Cliente", key="c_n"); cp = cc2.text_input("Projeto", "Proj", key="c_p")
                cc3, cc4, cc5 = st.columns(3); cv = cc3.text_input("Validade", "10 dias", key="c_v"); cpr = cc4.text_input("Prazo", "30 dias", key="c_pr"); cpg = cc5.text_input("Pagto", "50/50", key="c_pg")
            
            # --- ÁREA DE DOWNLOADS (PDF E EXCEL) ---
            st.divider()
            col_pdf, col_xls = st.columns(2)
            
            with col_pdf:
                if st.button("📄 Gerar PDF da Proposta", type="primary", key="btn_pdf", use_container_width=True):
                    lt = None
                    if logo:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f: f.write(logo.read()); lt = f.name
                    pdf = PropostaPDF({'nome':en, 'endereco':ee, 'telefone':et, 'email':em, 'site':es}, {'nome':cn, 'projeto':cp, 'validade':cv, 'prazo':cpr, 'pagamento':cpg}, lt)
                    pdf.add_page(); pdf.chapter_info(); pdf.chapter_tab(fin); pdf.chapter_end()
                    pf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); pdf.output(pf.name)
                    with open(pf.name, "rb") as f: st.download_button("📥 Baixar PDF Agora", f, f"Proposta_{cn}.pdf", mime="application/pdf", key="dl_pdf_real", type="secondary", use_container_width=True)
                    if lt: os.remove(lt)
            
            with col_xls:
                # Gera o arquivo Excel em memória
                excel_data = convert_df_to_excel(fin)
                st.download_button(
                    label="📥 Baixar Tabela Excel (.xlsx)",
                    data=excel_data,
                    file_name=f"Orcamento_{cn}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

if st.session_state.admin_logged_in:
    with tabs[1]:
        st.header("🛠️ Kits (Salva no Google Sheets)")
        kits_disp = sorted(db["Kits"]['ID_Kit'].unique()) if not db["Kits"].empty else []
        c_k1, c_k2 = st.columns([2, 1])
        if kits_disp:
            k_sel = c_k1.selectbox("Selecione:", kits_disp, key="sel_kit_a")
        else:
            k_sel = None
            c_k1.warning("Nenhum kit encontrado.")

        novo_k = c_k2.text_input("Novo Kit:", key="new_kit_a")
        if c_k2.button("Criar", key="btn_new_kit") and novo_k:
            new_row = pd.DataFrame({'ID_Kit':[novo_k], 'ID_Material':[''], 'Quantidade':[0]})
            db["Kits"] = pd.concat([db["Kits"], new_row], ignore_index=True)
            save_data_to_sheets("Kits", db["Kits"])
            st.rerun()
        
        if k_sel:
            if novo_k in kits_disp: k_sel = novo_k
            df_k = db["Kits"][db["Kits"]['ID_Kit'] == k_sel].copy()
            df_v = pd.merge(df_k, db["Materiais"][['ID_Material', 'Descricao']], on='ID_Material', how='left')
            
            st.subheader(f"Itens: {k_sel}")
            st.info("Para remover, selecione a linha e pressione DELETE.")
            
            df_ed = st.data_editor(
                df_v[['ID_Material', 'Descricao', 'Quantidade']],
                column_config={
                    "ID_Material": st.column_config.TextColumn(disabled=True),
                    "Descricao": st.column_config.TextColumn(disabled=True),
                    "Quantidade": st.column_config.NumberColumn(min_value=0.0)
                }, num_rows="dynamic", key="ked", use_container_width=True
            )
            
            if st.button("💾 Salvar Alterações na Nuvem", key="btn_save_cloud"):
                db["Kits"] = db["Kits"][db["Kits"]['ID_Kit'] != k_sel] 
                n = df_ed.copy(); n['ID_Kit'] = k_sel; n = n[n['ID_Material'] != '']
                db["Kits"] = pd.concat([db["Kits"], n[['ID_Kit', 'ID_Material', 'Quantidade']]], ignore_index=True)
                save_data_to_sheets("Kits", db["Kits"])
                st.rerun()
                
            st.divider()
            st.markdown("#### ➕ Adicionar Material")
            ca1, ca2, ca3 = st.columns([3, 1, 1])
            opts = db["Materiais"].apply(lambda x: f"{x['Descricao']} | {x['ID_Material']}", axis=1)
            add_itm = ca1.selectbox("Item:", opts, key="add_itm_sel")
            add_qtd = ca2.number_input("Qtd:", 1.0, key="add_qtd_num")
            if ca3.button("Adicionar", key="btn_add_k"):
                id_add = add_itm.split(" | ")[-1]
                new_row = pd.DataFrame({'ID_Kit':[k_sel], 'ID_Material':[id_add], 'Quantidade':[add_qtd]})
                db["Kits"] = pd.concat([db["Kits"], new_row], ignore_index=True)
                save_data_to_sheets("Kits", db["Kits"])
                st.rerun()

    with tabs[2]:
        st.header("🗃️ Banco de Dados (Nuvem)")
        st.info("⚠️ Qualquer alteração aqui reflete na Planilha Google.")
        t = st.selectbox("Tabela", list(SHEET_TABS.keys()), key="sel_tab_cloud")
        
        ed = st.data_editor(db[t], num_rows="dynamic", use_container_width=True, key="cloud_editor")
        
        if st.button("Salvar Tabela na Nuvem", key="btn_save_tab_cloud"):
            save_data_to_sheets(t, ed)
            st.rerun()
