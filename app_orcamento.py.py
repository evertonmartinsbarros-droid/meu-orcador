import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import tempfile
import os

# Tenta importar Plotly com segurança
try:
    import plotly.express as px
    PLOTLY_ATIVO = True
except ImportError:
    PLOTLY_ATIVO = False

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO
# ==============================================================================
st.set_page_config(page_title="Gerador de Propostas", page_icon="💼", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricValue"] { font-size: 24px; color: #00CC96; font-weight: bold; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 8px; }
    .stDataFrame { border: 1px solid #ddd; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. LOGIN
# ==============================================================================
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False

def check_login(u, p):
    if u == "admin" and p == "1234":
        st.session_state.admin_logged_in = True; st.rerun()
    else: st.sidebar.error("Senha incorreta")

def logout(): st.session_state.admin_logged_in = False; st.rerun()

# ==============================================================================
# 3. DADOS
# ==============================================================================
FILES = {
    "Materiais": "db_materiais.csv", "MaoDeObra": "db_mdo.csv", "Kits": "db_kits.csv",
    "Config_Acionamentos": "db_conf_acion.csv", "Config_Vasos": "db_conf_vasos.csv",
    "Config_Hidraulica": "db_conf_hidra.csv"
}

DEFAULT_DATA = {
    "Materiais": {
        'ID_Material': ['CLP-AUT-01', 'PAINEL-8060', 'CONT-MOT-12A', 'VASO-FIL-3072', 'VALV-BORB-E2', 'TUBO-PVC-2', 'MDO-MONT-ELET'],
        'Descricao': ['CLP Básico', 'Painel 80x60', 'Contator 12A', 'Vaso 30x72', 'Válvula 2pol', 'Tubo 2pol', 'Montagem'],
        'Grupo_Orcamento': ['CLP', 'Itens de Painel', 'Itens de Painel', 'Vasos', 'Hidráulica', 'Hidráulica', 'Mão de Obra'],
        'Preco_Custo': [2500.0, 750.0, 90.0, 6000.0, 700.0, 90.0, 80.0]
    },
    "MaoDeObra": {
        'ID_MaoDeObra': ['MDO-MONT-ELET', 'MDO-PROG-CLP', 'MDO-MONT-HIDR'],
        'Tipo_Servico': ['Montagem Elétrica', 'Programação CLP', 'Montagem Hidráulica'],
        'Grupo_Orcamento': ['Mão de Obra', 'Mão de Obra', 'Mão de Obra'],
        'Custo_Hora': [80.0, 150.0, 70.0]
    },
    "Config_Acionamentos": {
        'Num_Vasos': [1, 2, 3, 4],
        'ID_Material_CLP': ['CLP-AUT-01', 'CLP-AUT-01', 'CLP-AUT-02', 'CLP-AUT-02'],
        'ID_Material_Painel': ['PAINEL-8060', 'PAINEL-8060', 'PAINEL-10060', 'PAINEL-10080'],
        'ID_Material_IHM': ['IHM-AUT-7POL', 'IHM-AUT-7POL', 'IHM-AUT-10POL', 'IHM-AUT-10POL'],
        'ID_Kit_Painel_Eletrico': ['KIT-PAINEL-1V', 'KIT-PAINEL-2V', 'KIT-PAINEL-3V', 'KIT-PAINEL-4V'],
        'Horas_MDO_Mont_Elet': [16, 24, 32, 40], 'Horas_MDO_Prog_CLP': [10, 16, 24, 30]
    },
    "Config_Vasos": {
        'Descricao_Vaso': ['30x72', '36x72', '42x72', '48x72', '63x80'],
        'ID_Material_Vaso': ['VASO-FIL-3072', 'VASO-FIL-3672', 'VASO-FIL-4272', 'VASO-FIL-4872', 'VASO-FIL-6380'],
        'Horas_MDO_Hidr_p_Vaso': [16, 18, 20, 22, 25]
    },
    "Config_Hidraulica": {
        'Descricao_Vaso': ['30x72', '36x72', '36x72', '42x72', '42x72', '48x72', '48x72', '63x80', '63x80'],
        'ID_Diametro_mm': [50, 50, 100, 100, 150, 100, 150, 100, 150],
        'ID_Kit_Hidraulico_p_Vaso': [
            'KIT-HID-3072-PV-50MM', 'KIT-HID-3672-PV-50MM', 'KIT-HID-3672-PV-100MM',
            'KIT-HID-4272-PV-100MM', 'KIT-HID-4272-PV-150MM', 'KIT-HID-4872-PV-100MM',
            'KIT-HID-4872-PV-150MM', 'KIT-HID-6380-PV-100MM', 'KIT-HID-6380-PV-150MM'
        ]
    },
    "Kits": {'ID_Kit': [], 'ID_Material': [], 'Quantidade': []}
}

def load_data(force_reset=False):
    dfs = {}
    for k, f in FILES.items():
        if force_reset or not os.path.exists(f):
            df = pd.DataFrame(DEFAULT_DATA.get(k, {}))
            df.to_csv(f, index=False)
            dfs[k] = df
        else:
            try: dfs[k] = pd.read_csv(f)
            except: 
                df = pd.DataFrame(DEFAULT_DATA.get(k, {}))
                df.to_csv(f, index=False)
                dfs[k] = df
    return dfs

def save_data(k, df):
    df.to_csv(FILES[k], index=False)
    st.toast(f"✅ {k} salvo!", icon="💾")

db = load_data()

# ==============================================================================
# 4. PDF
# ==============================================================================
class PropostaPDF(FPDF):
    def __init__(self, emp, cli, logo=None):
        super().__init__(); self.emp = emp; self.cli = cli; self.logo = logo
    
    def header(self):
        if self.page_no() == 1:
            if self.logo:
                try: self.image(self.logo, 10, 8, 33)
                except: pass
            self.set_font('Arial', 'B', 12)
            self.cell(0, 5, self.emp['nome'], 0, 1, 'R')
            self.set_font('Arial', '', 9)
            self.cell(0, 5, self.emp['endereco'], 0, 1, 'R')
            self.cell(0, 5, f"Tel: {self.emp['telefone']} | Email: {self.emp['email']}", 0, 1, 'R')
            self.cell(0, 5, self.emp['site'], 0, 1, 'R')
            self.ln(10)
            self.set_font('Arial', 'B', 16); self.set_text_color(0, 51, 102)
            self.cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'C'); self.ln(5)
            self.set_text_color(0, 0, 0)
        else: self.ln(10)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_info(self):
        if self.page_no() == 1:
            self.set_fill_color(240, 240, 240); self.set_font('Arial', 'B', 10)
            self.cell(0, 8, " DADOS DO CLIENTE", 1, 1, 'L', 1)
            self.set_font('Arial', '', 10)
            self.cell(0, 6, f"Cliente: {self.cli['nome']}", 0, 1)
            self.cell(0, 6, f"Projeto: {self.cli['projeto']}", 0, 1)
            self.cell(0, 6, f"Validade: {self.cli['validade']}", 0, 1); self.ln(5)

    def chapter_tab(self, df):
        self.set_fill_color(0, 51, 102); self.set_text_color(255); self.set_font('Arial', 'B', 9)
        self.cell(100, 8, "Item", 1, 0, 'L', 1); self.cell(20, 8, "Qtd", 1, 0, 'C', 1)
        self.cell(35, 8, "Unit (R$)", 1, 0, 'R', 1); self.cell(35, 8, "Total (R$)", 1, 1, 'R', 1)
        self.set_text_color(0); self.set_font('Arial', '', 9); fill = False
        for _, r in df.iterrows():
            self.set_fill_color(245); self.cell(100, 7, str(r['Descrição'])[:55], 1, 0, 'L', fill)
            self.cell(20, 7, str(r['Qtd']), 1, 0, 'C', fill)
            self.cell(35, 7, f"{r['Venda Unit']:,.2f}", 1, 0, 'R', fill)
            self.cell(35, 7, f"{r['Total Venda']:,.2f}", 1, 1, 'R', fill); fill = not fill
        self.ln(2); self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"TOTAL: R$ {df['Total Venda'].sum():,.2f}", 0, 1, 'R'); self.ln(5)

    def chapter_end(self):
        self.set_font('Arial', 'B', 10); self.set_fill_color(240)
        self.cell(0, 8, " CONDIÇÕES", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, f"Prazo: {self.cli['prazo']}\nPagamento: {self.cli['pagamento']}")
        self.ln(20); y = self.get_y()
        self.line(20, y, 90, y); self.line(120, y, 190, y)
        self.cell(95, 5, self.emp['nome'], 0, 0, 'C'); self.cell(95, 5, "Cliente", 0, 1, 'C')

# ==============================================================================
# 5. CÁLCULO
# ==============================================================================
def calc(n, t, d, m):
    try:
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
    except: return None

# ==============================================================================
# 6. APP
# ==============================================================================
with st.sidebar:
    st.title("🛡️ Admin")
    if not st.session_state.admin_logged_in:
        u = st.text_input("User", key="login_u"); p = st.text_input("Pass", type="password", key="login_p")
        if st.button("Entrar", key="btn_login"): check_login(u, p)
    else:
        st.success("Logado"); 
        if st.button("Sair", key="btn_logout"): logout()
        st.divider()
        logo = st.file_uploader("Logo", type=['png', 'jpg'], key="upl_logo")
        if logo: st.image(logo, width=150)
        with st.expander("Empresa"):
            en = st.text_input("Nome", "Empresa Ltda", key="emp_n")
            ee = st.text_input("End", "Rua X", key="emp_e")
            et = st.text_input("Tel", "(11) 999", key="emp_t")
            em = st.text_input("Email", "contato@", key="emp_em")
            es = st.text_input("Site", "www", key="emp_s")
        st.divider()
        if st.button("⚠️ Reset", key="btn_reset"): load_data(True); st.rerun()
    if not st.session_state.admin_logged_in: logo, en, ee, et, em, es = None, "Empresa", "", "", "", ""

tabs = st.tabs(["📊 Proposta", "🛠️ Kits", "🗃️ Dados"]) if st.session_state.admin_logged_in else st.tabs(["📊 Proposta"])

with tabs[0]:
    st.title("Gerador de Propostas")
    c1, c2, c3 = st.columns(3)
    nv = c1.selectbox("Vasos", [1,2,3,4], index=3, key="sel_vasos")
    tv = c2.selectbox("Tamanho", db["Config_Vasos"]['Descricao_Vaso'].unique(), index=3, key="sel_tam")
    dt = c3.selectbox("Diâmetro", db["Config_Hidraulica"]['ID_Diametro_mm'].unique(), index=1, key="sel_dia")
    
    st.divider()
    with st.expander("⚙️ Margens (%)", expanded=True):
        cm = st.columns(7)
        # --- AQUI ESTAVA O ERRO (CORRIGIDO COM NOMES ÚNICOS E KEYS) ---
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
    if df is None: st.error("Erro config")
    else:
        st.divider()
        edited = st.data_editor(
            df, 
            column_config={
                "Incluir": st.column_config.CheckboxColumn(width="small"), 
                "Custo Unit": st.column_config.NumberColumn(format="R$ %.2f"), 
                "Venda Unit": st.column_config.NumberColumn(format="R$ %.2f"), 
                "Total Venda": st.column_config.NumberColumn(format="R$ %.2f")
            }, 
            disabled=["Descrição", "Grupo", "Qtd", "Custo Unit", "Venda Unit", "Total Venda"], 
            hide_index=True, use_container_width=True, key="main_editor"
        )
        
        fin = edited[edited['Incluir']].copy()
        vt = fin['Total Venda'].sum(); ct = fin['Total Custo'].sum(); lc = vt - ct
        lp = (lc/ct*100) if ct>0 else 0
        
        st.divider()
        c_k, c_g = st.columns([1,1])
        with c_k:
            k1, k2 = st.columns(2); k1.metric("Venda", f"R$ {vt:,.2f}"); k2.metric("Custo", f"R$ {ct:,.2f}")
            k3, k4 = st.columns(2); k3.metric("Lucro", f"R$ {lc:,.2f}"); k4.metric("Margem", f"{lp:.1f}%")
        with c_g:
            if PLOTLY_ATIVO and lc > 0:
                g = fin.groupby("Grupo")[["Total Venda", "Total Custo"]].sum().reset_index()
                g["L"] = g["Total Venda"] - g["Total Custo"]
                fig = px.pie(g, values="L", names="Grupo", hole=0.4); fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig, use_container_width=True)
            elif not PLOTLY_ATIVO: st.warning("Sem Plotly")
            else: st.info("Sem lucro")

        st.divider()
        with st.expander("📝 Cliente", expanded=False):
            cc1, cc2 = st.columns(2)
            cn = cc1.text_input("Nome", "Cliente", key="cli_n"); cp = cc2.text_input("Projeto", "Proj", key="cli_p")
            cc3, cc4, cc5 = st.columns(3)
            cv = cc3.text_input("Validade", "10 dias", key="cli_v"); cpr = cc4.text_input("Prazo", "30 dias", key="cli_pr"); cpg = cc5.text_input("Pagto", "50/50", key="cli_pg")

        if st.button("📄 PDF", type="primary", key="btn_pdf"):
            lt = None
            if logo:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f: f.write(logo.read()); lt = f.name
            pdf = PropostaPDF({'nome':en, 'endereco':ee, 'telefone':et, 'email':em, 'site':es}, {'nome':cn, 'projeto':cp, 'validade':cv, 'prazo':cpr, 'pagamento':cpg}, lt)
            pdf.add_page(); pdf.chapter_info(); pdf.chapter_tab(fin); pdf.chapter_end()
            pf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); pdf.output(pf.name)
            with open(pf.name, "rb") as f: st.download_button("Download PDF", f, "orc.pdf")
            if lt: os.remove(lt)

if st.session_state.admin_logged_in:
    with tabs[1]:
        st.header("🛠️ Editor de Kits")
        
        kits_disp = sorted(db["Kits"]['ID_Kit'].unique())
        c_k1, c_k2 = st.columns([2, 1])
        k_sel = c_k1.selectbox("Selecione:", kits_disp, key="sel_kit_adm")
        novo_k = c_k2.text_input("Novo Kit:", key="inp_new_kit")
        if c_k2.button("Criar", key="btn_crt_kit"):
            if novo_k not in kits_disp:
                db["Kits"] = pd.concat([db["Kits"], pd.DataFrame({'ID_Kit':[novo_k], 'ID_Material':[''], 'Quantidade':[0]})], ignore_index=True)
                save_data("Kits", db["Kits"]); st.rerun()
        if novo_k in kits_disp: k_sel = novo_k

        st.subheader(f"Itens: {k_sel}")
        st.info("💡 Para remover: Selecione a linha e aperte DELETE no teclado.")
        
        df_k = db["Kits"][db["Kits"]['ID_Kit'] == k_sel].copy()
        df_v = pd.merge(df_k, db["Materiais"][['ID_Material', 'Descricao']], on='ID_Material', how='left')
        
        df_ed = st.data_editor(
            df_v[['ID_Material', 'Descricao', 'Quantidade']],
            column_config={
                "ID_Material": st.column_config.TextColumn(disabled=True),
                "Descricao": st.column_config.TextColumn(disabled=True),
                "Quantidade": st.column_config.NumberColumn(min_value=0.0)
            },
            num_rows="dynamic", key="ked", use_container_width=True
        )
        
        if st.button("💾 Salvar Alterações (Qtd/Remoção)", key="btn_save_kit"):
            db["Kits"] = db["Kits"][db["Kits"]['ID_Kit'] != k_sel]
            n = df_ed.copy(); n['ID_Kit'] = k_sel; n = n[n['ID_Material'] != '']
            db["Kits"] = pd.concat([db["Kits"], n[['ID_Kit', 'ID_Material', 'Quantidade']]], ignore_index=True)
            save_data("Kits", db["Kits"]); st.success("Salvo!"); st.rerun()
        
        st.divider()
        st.markdown("#### ➕ Adicionar Material ao Kit")
        ca1, ca2, ca3 = st.columns([3, 1, 1])
        opts = db["Materiais"].apply(lambda x: f"{x['Descricao']} | {x['ID_Material']}", axis=1)
        add_itm = ca1.selectbox("Item:", opts, key="sel_add_item")
        add_qtd = ca2.number_input("Qtd:", 1.0, key="num_add_qtd")
        if ca3.button("Adicionar", key="btn_add_item"):
            id_add = add_itm.split(" | ")[-1]
            db["Kits"] = pd.concat([db["Kits"], pd.DataFrame({'ID_Kit':[k_sel], 'ID_Material':[id_add], 'Quantidade':[add_qtd]})], ignore_index=True)
            save_data("Kits", db["Kits"]); st.toast("Adicionado!"); st.rerun()

    with tabs[2]:
        st.header("Dados"); t = st.selectbox("Tabela", list(FILES.keys()), key="sel_db_tab")
        ed = st.data_editor(db[t], num_rows="dynamic", use_container_width=True, key="db_editor")
        if st.button("Salvar DB", key="btn_save_db"): save_data(t, ed); st.rerun()
