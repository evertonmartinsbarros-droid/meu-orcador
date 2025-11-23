import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import tempfile
import os
import plotly.express as px  # Nova biblioteca para gráficos bonitos

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO (DESIGN MODERNO)
# ==============================================================================
st.set_page_config(page_title="Gerador de Propostas", page_icon="💼", layout="wide")

st.markdown("""
<style>
    /* Fundo geral levemente cinza para destacar os cartões */
    .stApp {
        background-color: #F8F9FA;
    }

    /* Estilo dos Cartões de Métricas (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: 0.3s;
    }
    
    /* Efeito ao passar o mouse nos cartões */
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        border-color: #00CC96;
        transform: translateY(-2px);
    }

    /* Cores e fontes dos números */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #00CC96;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        font-size: 15px;
        color: #6c757d;
        font-weight: 500;
    }

    /* Botões mais bonitos */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* Ajuste da Tabela */
    .stDataFrame { 
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE LOGIN E SEGURANÇA
# ==============================================================================
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

def check_login(user, password):
    if user == "admin" and password == "1234":
        st.session_state.admin_logged_in = True
        st.rerun()
    else:
        st.sidebar.error("Senha incorreta")

def logout():
    st.session_state.admin_logged_in = False
    st.rerun()

# ==============================================================================
# 3. DADOS E ARQUIVOS
# ==============================================================================
FILES = {
    "Materiais": "db_materiais.csv",
    "MaoDeObra": "db_mdo.csv",
    "Kits": "db_kits.csv",
    "Config_Acionamentos": "db_conf_acion.csv",
    "Config_Vasos": "db_conf_vasos.csv",
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
        'Horas_MDO_Mont_Elet': [16, 24, 32, 40],
        'Horas_MDO_Prog_CLP': [10, 16, 24, 30]
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
    dataframes = {}
    for key, filename in FILES.items():
        if force_reset or not os.path.exists(filename):
            df = pd.DataFrame(DEFAULT_DATA.get(key, {}))
            df.to_csv(filename, index=False)
            dataframes[key] = df
        else:
            try:
                dataframes[key] = pd.read_csv(filename)
            except:
                df = pd.DataFrame(DEFAULT_DATA.get(key, {}))
                df.to_csv(filename, index=False)
                dataframes[key] = df
    return dataframes

def save_data(key, df):
    df.to_csv(FILES[key], index=False)
    st.toast(f"✅ {key} salvo!", icon="💾")

db = load_data()

# ==============================================================================
# 4. CLASSE PDF (Profissional)
# ==============================================================================
class PropostaPDF(FPDF):
    def __init__(self, empresa_dados, cliente_dados, logo_path=None):
        super().__init__()
        self.empresa = empresa_dados
        self.cliente = cliente_dados
        self.logo_path = logo_path

    def header(self):
        # Apenas na primeira página
        if self.page_no() == 1:
            if self.logo_path:
                try: self.image(self.logo_path, 10, 8, 33)
                except: pass
            
            # Dados Empresa
            self.set_font('Arial', 'B', 12)
            self.cell(0, 5, self.empresa['nome'], 0, 1, 'R')
            self.set_font('Arial', '', 9)
            self.cell(0, 5, self.empresa['endereco'], 0, 1, 'R')
            self.cell(0, 5, f"Tel: {self.empresa['telefone']} | Email: {self.empresa['email']}", 0, 1, 'R')
            self.cell(0, 5, self.empresa['site'], 0, 1, 'R')
            self.ln(10)
            
            # Título
            self.set_font('Arial', 'B', 16)
            self.set_text_color(0, 51, 102)
            self.cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'C')
            self.ln(5)
            self.set_text_color(0, 0, 0)
        else:
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_info_cliente(self):
        if self.page_no() == 1:
            self.set_fill_color(240, 240, 240)
            self.set_font('Arial', 'B', 10)
            self.cell(0, 8, " DADOS DO CLIENTE", 1, 1, 'L', 1)
            self.set_font('Arial', '', 10)
            self.cell(0, 6, f"Cliente: {self.cliente['nome']}", 0, 1)
            self.cell(0, 6, f"Projeto: {self.cliente['projeto']}", 0, 1)
            self.cell(0, 6, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Validade: {self.cliente['validade']}", 0, 1)
            self.ln(5)

    def chapter_tabela(self, df):
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 9)
        self.cell(100, 8, "Item / Descrição", 1, 0, 'L', 1)
        self.cell(20, 8, "Qtd", 1, 0, 'C', 1)
        self.cell(35, 8, "Unitário (R$)", 1, 0, 'R', 1)
        self.cell(35, 8, "Total (R$)", 1, 1, 'R', 1)
        
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)
        fill = False
        for _, row in df.iterrows():
            self.set_fill_color(245, 245, 245)
            self.cell(100, 7, str(row['Descrição'])[0:55], 1, 0, 'L', fill)
            self.cell(20, 7, str(row['Qtd']), 1, 0, 'C', fill)
            self.cell(35, 7, f"{row['Venda Unit']:,.2f}", 1, 0, 'R', fill)
            self.cell(35, 7, f"{row['Total Venda']:,.2f}", 1, 1, 'R', fill)
            fill = not fill 
        
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"VALOR TOTAL: R$ {df['Total Venda'].sum():,.2f}", 0, 1, 'R')
        self.ln(5)

    def chapter_condicoes(self):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, " CONDIÇÕES COMERCIAIS", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, f"Prazo de Entrega: {self.cliente['prazo']}")
        self.multi_cell(0, 6, f"Pagamento: {self.cliente['pagamento']}")
        self.ln(20)
        self.set_font('Arial', '', 10)
        y = self.get_y()
        self.line(20, y, 90, y)
        self.line(120, y, 190, y)
        self.cell(95, 5, self.empresa['nome'], 0, 0, 'C')
        self.cell(95, 5, "De Acordo (Cliente)", 0, 1, 'C')

# ==============================================================================
# 5. CÁLCULO
# ==============================================================================
def calcular_itens(num_vasos, tam_vaso, diametro, margens_dict):
    try:
        regra_painel = db["Config_Acionamentos"][db["Config_Acionamentos"]['Num_Vasos'] == num_vasos].iloc[0]
        regra_vaso = db["Config_Vasos"][db["Config_Vasos"]['Descricao_Vaso'] == tam_vaso].iloc[0]
        df_hidra = db["Config_Hidraulica"]
        filtro_hid = (df_hidra['Descricao_Vaso'] == tam_vaso) & (df_hidra['ID_Diametro_mm'] == diametro)
        
        if filtro_hid.sum() == 0: return None
        
        id_kit_hidra = df_hidra[filtro_hid].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        id_kit_painel = regra_painel['ID_Kit_Painel_Eletrico']

        itens = []
        # Base
        itens.append({'ID': regra_painel['ID_Material_CLP'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_painel['ID_Material_Painel'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_painel['ID_Material_IHM'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_vaso['ID_Material_Vaso'], 'Qtd': num_vasos, 'Tipo': 'Material'})
        
        # Kits
        df_kits = db["Kits"]
        for k, f in [(id_kit_painel, 1), (id_kit_hidra, num_vasos)]:
            k_itens = df_kits[df_kits['ID_Kit'] == k]
            for _, r in k_itens.iterrows():
                itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'] * f, 'Tipo': 'Material'})

        # MDO
        itens.append({'ID': 'MDO-MONT-ELET', 'Qtd': regra_painel['Horas_MDO_Mont_Elet'], 'Tipo': 'MDO'})
        itens.append({'ID': 'MDO-PROG-CLP', 'Qtd': regra_painel['Horas_MDO_Prog_CLP'], 'Tipo': 'MDO'})
        itens.append({'ID': 'MDO-MONT-HIDR', 'Qtd': regra_vaso['Horas_MDO_Hidr_p_Vaso'] * num_vasos, 'Tipo': 'MDO'})

        res = []
        df_mat, df_mdo = db["Materiais"], db["MaoDeObra"]

        for item in itens:
            if item['Tipo'] == 'Material':
                d = df_mat[df_mat['ID_Material'] == item['ID']]
                if d.empty: continue
                desc, grp, cust = d.iloc[0]['Descricao'], d.iloc[0]['Grupo_Orcamento'], float(d.iloc[0]['Preco_Custo'])
                mrg = margens_dict.get(grp, 0)
            else:
                d = df_mdo[df_mdo['ID_MaoDeObra'] == item['ID']]
                if d.empty: continue
                desc, grp, cust = d.iloc[0]['Tipo_Servico'], "Mão de Obra", float(d.iloc[0]['Custo_Hora'])
                if item['ID'] == 'MDO-MONT-ELET': mrg = margens_dict.get("MDO_Elet", 0)
                elif item['ID'] == 'MDO-PROG-CLP': mrg = margens_dict.get("MDO_Prog", 0)
                elif item['ID'] == 'MDO-MONT-HIDR': mrg = margens_dict.get("MDO_Hidr", 0)
                else: mrg = 0

            unit_venda = cust * (1 + (mrg/100))
            tot_cust = cust * item['Qtd']
            tot_vend = unit_venda * item['Qtd']
            
            res.append({'Incluir': True, 'Descrição': desc, 'Grupo': grp, 'Qtd': item['Qtd'], 'Custo Unit': cust, 'Venda Unit': unit_venda, 'Total Venda': tot_vend, 'Total Custo': tot_cust})

        return pd.DataFrame(res)
    except:
        return None

# ==============================================================================
# 6. INTERFACE
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Admin")
    
    if not st.session_state.admin_logged_in:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"): check_login(u, p)
    else:
        st.success("Logado como Admin")
        if st.button("Sair"): logout()
        st.divider()
        st.header("Empresa")
        emp_logo = st.file_uploader("Logo", type=['png', 'jpg'])
        if emp_logo: st.image(emp_logo, caption="Logo", use_container_width=True)
        with st.expander("Dados", expanded=False):
            emp_nome = st.text_input("Nome", "Sua Empresa")
            emp_end = st.text_input("Endereço", "Rua...")
            emp_tel = st.text_input("Tel", "...")
            emp_email = st.text_input("Email", "...")
            emp_site = st.text_input("Site", "...")
        st.divider()
        if st.button("⚠️ Resetar Tudo"): load_data(True); st.rerun()

    if not st.session_state.admin_logged_in:
        emp_logo, emp_nome, emp_end, emp_tel, emp_email, emp_site = None, "Empresa", "", "", "", ""

# --- TABS ---
if st.session_state.admin_logged_in:
    tab_dash, tab_kits, tab_db = st.tabs(["📊 Dashboard & Proposta", "🛠️ Kits", "🗃️ Dados"])
else:
    tab_dash, = st.tabs(["📊 Dashboard & Proposta"])

# --- DASHBOARD ---
with tab_dash:
    st.title("Gerador de Proposta Comercial")
    
    c1, c2, c3 = st.columns(3)
    with c1: sel_vasos = st.selectbox("Nº Vasos", [1,2,3,4], index=3)
    with c2: sel_tamanho = st.selectbox("Tamanho", db["Config_Vasos"]['Descricao_Vaso'].unique(), index=3)
    with c3: sel_diametro = st.selectbox("Diâmetro", db["Config_Hidraulica"]['ID_Diametro_mm'].unique(), index=1)
    
    st.divider()
    
    # Margens
    with st.expander("⚙️ Ajustar Margens de Lucro (%)", expanded=True):
        col_m = st.columns(7)
        m_clp = col_m[0].number_input("CLP", 0, 500, 50)
        m_painel = col_m[1].number_input("Painel", 0, 500, 50)
        m_hidra = col_m[2].number_input("Hidr.", 0, 500, 50)
        m_vasos = col_m[3].number_input("Vasos", 0, 500, 50)
        m_elet = col_m[4].number_input("MDO E.", 0, 500, 50)
        m_prog = col_m[5].number_input("MDO P.", 0, 500, 50)
        m_mont_h = col_m[6].number_input("MDO H.", 0, 500, 50)

    MARGENS = {"CLP": m_clp, "Itens de Painel": m_painel, "Hidráulica": m_hidra, "Vasos": m_vasos, "MDO_Elet": m_elet, "MDO_Prog": m_prog, "MDO_Hidr": m_mont_h}
    
    df_inicial = calcular_itens(sel_vasos, sel_tamanho, sel_diametro, MARGENS)
    
    if df_inicial is None:
        st.error("❌ Configuração não encontrada.")
    else:
        st.divider()
        st.subheader("📋 Seleção de Itens")
        
        df_editado = st.data_editor(
            df_inicial,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Incluir", width="small"),
                "Custo Unit": st.column_config.NumberColumn(format="R$ %.2f"),
                "Venda Unit": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total Venda": st.column_config.NumberColumn(format="R$ %.2f")
            },
            disabled=["Descrição", "Grupo", "Qtd", "Custo Unit", "Venda Unit", "Total Venda"],
            hide_index=True,
            use_container_width=True
        )
        
        # CÁLCULOS FINAIS
        df_final = df_editado[df_editado['Incluir'] == True].copy()
        venda_total = df_final['Total Venda'].sum()
        custo_total = df_final['Total Custo'].sum()
        lucro = venda_total - custo_total
        lucro_pct = (lucro / custo_total * 100) if custo_total > 0 else 0
        
        # --- ÁREA DE KPIS E GRÁFICO ---
        st.divider()
        
        col_kpi, col_chart = st.columns([1, 1])
        
        with col_kpi:
            st.markdown("#### 💹 Resumo Financeiro")
            # Exibindo como "cartões" (estilizados pelo CSS lá em cima)
            k1, k2 = st.columns(2)
            k1.metric("Valor Venda", f"R$ {venda_total:,.2f}")
            k2.metric("Custo Total", f"R$ {custo_total:,.2f}")
            
            k3, k4 = st.columns(2)
            k3.metric("Lucro Líquido", f"R$ {lucro:,.2f}")
            k4.metric("Margem %", f"{lucro_pct:.1f}%")
        
        with col_chart:
            st.markdown("#### 🍰 Distribuição do Lucro")
            # Gráfico de Pizza com Plotly
            # Agrupa dados por Grupo
            df_chart = df_final.groupby("Grupo")[["Total Venda", "Total Custo"]].sum().reset_index()
            df_chart["Lucro"] = df_chart["Total Venda"] - df_chart["Total Custo"]
            
            # Gráfico
            fig = px.pie(df_chart, values="Lucro", names="Grupo", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
            st.plotly_chart(fig, use_container_width=True)

        # PDF
        st.divider()
        with st.expander("📄 Dados do Cliente para PDF", expanded=False):
            c_pdf1, c_pdf2 = st.columns(2)
            cli_nome = c_pdf1.text_input("Cliente", "Nome do Cliente")
            cli_proj = c_pdf2.text_input("Projeto", "Projeto Exemplo")
            c_pdf3, c_pdf4, c_pdf5 = st.columns(3)
            cli_val = c_pdf3.date_input("Validade", datetime.now() + timedelta(days=10))
            cli_prazo = c_pdf4.text_input("Prazo", "30 dias")
            cli_pag = c_pdf5.text_input("Pagamento", "50% Entrada")

        if st.button("🖨️ GERAR PDF DA PROPOSTA", type="primary"):
            logo_tmp = None
            if emp_logo:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                    f.write(emp_logo.read()); logo_tmp = f.name
            
            dd_emp = {'nome':emp_nome, 'endereco':emp_end, 'telefone':emp_tel, 'email':emp_email, 'site':emp_site}
            dd_cli = {'nome':cli_nome, 'projeto':cli_proj, 'validade':cli_val.strftime('%d/%m/%Y'), 'prazo':cli_prazo, 'pagamento':cli_pag}
            
            pdf = PropostaPDF(dd_emp, dd_cli, logo_tmp)
            pdf.add_page(); pdf.chapter_info_cliente(); pdf.chapter_tabela(df_final); pdf.chapter_condicoes()
            
            pfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf.output(pfile.name)
            with open(pfile.name, "rb") as f: st.download_button("📥 Baixar PDF", f, f"Proposta_{cli_nome}.pdf", "application/pdf")
            if logo_tmp: os.remove(logo_tmp)

# --- OUTRAS ABAS (ADMIN) ---
if st.session_state.admin_logged_in:
    with tab_kits:
        st.header("Editor de Kits"); k_sel = st.selectbox("Kit", sorted(db["Kits"]['ID_Kit'].unique()))
        df_k = db["Kits"][db["Kits"]['ID_Kit']==k_sel].merge(db["Materiais"][['ID_Material','Descricao']], on='ID_Material', how='left')
        df_ed = st.data_editor(df_k[['ID_Material','Descricao','Quantidade']], num_rows="dynamic", key="ked")
        if st.button("Salvar Kit"):
            db["Kits"] = db["Kits"][db["Kits"]['ID_Kit']!=k_sel]
            n = df_ed.copy(); n['ID_Kit']=k_sel; n=n[n['ID_Material']!='']
            db["Kits"] = pd.concat([db["Kits"], n[['ID_Kit','ID_Material','Quantidade']]], ignore_index=True)
            save_data("Kits", db["Kits"]); st.rerun()
    with tab_db:
        t = st.selectbox("DB", list(FILES.keys())); e = st.data_editor(db[t], num_rows="dynamic")
        if st.button("Salvar DB"): save_data(t, e); st.rerun()
